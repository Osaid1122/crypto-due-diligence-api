"""
Deterministic risk scoring engine.

Rules and weights below were tuned against real GoPlus responses for USDC, LINK,
UNI (see tests/fixtures/real_goplus_samples.py), not just documentation. Two
things changed after seeing real data:

1. is_proxy alone is common on legitimate large tokens (USDC is a proxy) — it's
   informational on its own, only escalated when paired with hidden_owner or
   can_take_back_ownership (upgradeable + no accountability is the real risk).
2. Liquidity risk is now based on LP concentration/fragmentation, not a binary
   "is any LP position locked" flag — that flag alone flagged LINK (10+ genuine,
   unrelated LP positions) as "unlocked", which is a false positive on one of the
   most liquid tokens in crypto. Fragmented liquidity across many LPs is healthy
   even if none used a locker contract; 1-2 dominant LP positions is the real signal.
"""

from typing import Any

CHECKS: list[tuple[str, bool, int, str, str, str]] = [
    ("is_honeypot", True, 40, "Critical", "Token is flagged as a honeypot — it may be difficult or impossible to sell", "No honeypot detected"),
    ("is_mintable", True, 20, "High", "Contract owner can mint new tokens, diluting holder value at will", "No mint function detected"),
    ("cannot_sell_all", True, 15, "High", "Holders may not be able to sell their entire balance", "Full balance can be sold"),
    ("is_blacklisted", True, 15, "High", "Contract includes a blacklist function that can block specific wallets from trading", "No blacklist function detected"),
    ("hidden_owner", True, 15, "High", "Contract has a hidden owner — control may persist even if ownership looks renounced", "No hidden owner detected"),
    ("can_take_back_ownership", True, 15, "High", "Ownership can reportedly be reclaimed after being renounced", "Ownership cannot be reclaimed"),
    ("selfdestruct", True, 10, "Medium", "Contract contains a self-destruct function", "No self-destruct function detected"),
    ("trading_cooldown", True, 5, "Low", "Contract enforces a trading cooldown, which can restrict normal trading", "No trading cooldown detected"),
    ("is_open_source", False, 10, "Medium", "Contract source code is not verified/open source", "Contract source code verified"),
    # is_proxy downgraded to informational — common on legitimate large tokens (e.g. USDC)
    ("is_proxy", True, 3, "Informational", "Upgradeable proxy contract detected", "Not an upgradeable proxy"),

    # ---- Solana-only concepts (see solana_normalizer.py) — these keys are
    # never populated by the EVM normalizer, so they're always None for EVM
    # tokens and this section cannot change EVM scoring behavior. Weights
    # below are informed by one real data point: USDC on Solana (a
    # maximally-trusted token) has mintable/freezable enabled (normal
    # administrative capability even for trusted issuers) but closable and
    # balance_mutable_authority both disabled — suggesting the latter two
    # are NOT normal even for trusted tokens, and deserve materially higher
    # weight than mint/freeze. ----
    ("closable", True, 35, "Critical", "Contract can be closed by an authority, which would eliminate all associated assets — not enabled even on Solana's most trusted tokens", "Cannot be closed by an authority"),
    ("balance_mutable_authority", True, 30, "Critical", "An authority can directly alter individual holder balances — not enabled even on Solana's most trusted tokens", "No authority can alter holder balances directly"),
    # has_transfer_hook: Token-2022's programmable hooks can block trades
    # outright — the closest Solana analog to a honeypot. Weighted High
    # rather than Critical since we don't yet have a real example of a
    # token that uses this feature to see whether it's normal or abusive
    # in practice; revisit once one is observed.
    ("has_transfer_hook", True, 25, "High", "Token uses a transfer hook program, which can intercept or block transfers", "No transfer hook detected"),
    ("metadata_mutable", True, 8, "Low", "Token metadata (name, symbol, image) can be changed after launch", "Token metadata is immutable"),
    # Mint/freeze authority — deliberately NOT scored via the shared
    # is_mintable/is_blacklisted rules above (see solana_normalizer.py for
    # why). Real data (USDC on Solana) shows both present on a maximally-
    # trusted token, so weighted low/Informational like EVM's is_proxy,
    # not High like EVM's is_mintable. Revisit once a real risky Solana
    # token's data is available to check whether escalating via a combo
    # (e.g. mint+freeze together with no trust_list) is justified — no such
    # data point exists yet, so no combo rule is added speculatively.
    ("has_mint_authority", True, 5, "Informational", "Mint authority has not been revoked — the issuer can create additional tokens", "Mint authority has been revoked"),
    ("has_freeze_authority", True, 5, "Informational", "Freeze authority has not been revoked — the issuer can freeze individual holder accounts", "Freeze authority has been revoked"),
]

CRITICAL_COMBOS: list[tuple[set, str]] = [
    ({"is_honeypot", "cannot_sell_all"}, "Token appears to trap funds — flagged as a honeypot AND unable to sell in full"),
    ({"is_honeypot", "is_blacklisted"}, "Token can both block specific wallets and trap funds entirely"),
    ({"is_proxy", "hidden_owner"}, "Upgradeable contract combined with a hidden owner — control can change with no visible accountability"),
    ({"is_proxy", "can_take_back_ownership"}, "Upgradeable contract combined with reclaimable ownership — high potential for rug pull via upgrade"),
]

# Ordered risk bands, lowest → highest, so two candidate levels can be compared
# by index and the more severe one kept.
LEVELS: list[str] = ["Low", "Medium", "High", "Critical"]

# The floor a single triggered rule of a given severity places on the overall
# risk_level, independent of the numeric score. This is the fix for the core
# miscalibration: previously risk_level was derived from the point total ALONE,
# so a lone Critical-severity finding that happened to carry few points (e.g.
# liquidity concentration = 25 pts) surfaced as "Low" — the numeric roll-up
# silently outvoted the severity label. Now a Critical finding forces at least
# "High" and a High finding at least "Medium", whatever the score. Deliberately
# NOT "Critical → Critical": a single catastrophic-but-isolated flag is High;
# "Critical" is reserved for a named CRITICAL_COMBO or two independent Criticals
# (see MULTI_CRITICAL escalation below), matching the existing combo semantics.
SEVERITY_FLOOR: dict[str, str] = {
    "Critical": "High",
    "High": "Medium",
    "Medium": "Low",
    "Low": "Low",
    "Informational": "Low",
}

# Two or more INDEPENDENT Critical-severity findings escalate to Critical, the
# same outcome the named CRITICAL_COMBOS already produce — generalized so any
# pair of unrelated Critical flags (e.g. closable + balance_mutable_authority on
# Solana) is treated as seriously as a hand-listed EVM combo.
MULTI_CRITICAL_MIN_SCORE = 90


def _max_level(a: str, b: str) -> str:
    return a if LEVELS.index(a) >= LEVELS.index(b) else b


def score_token(normalized: dict) -> dict[str, Any]:
    score = 0
    triggered_rules: list[dict] = []
    not_triggered_rules: list[dict] = []
    positive_signals: list[str] = []
    reasons: list[str] = []
    triggered_field_names: set = set()

    for field, trigger_value, points, severity, reason, clean_label in CHECKS:
        value = normalized.get(field)
        if value is None:
            continue
        if value == trigger_value:
            score += points
            triggered_field_names.add(field)
            triggered_rules.append({"field": field, "value": value, "points": points, "severity": severity, "reason": reason})
            reasons.append(reason)
        else:
            not_triggered_rules.append({"field": field, "value": value, "reason": clean_label})

    # Holder concentration (burn addresses already excluded in normalizer)
    top_pct = normalized.get("top_holder_percent")
    if top_pct is not None:
        if top_pct >= 50:
            points, severity = 20, "High"
            reason = f"Top holder controls {top_pct:.0f}% of circulating supply — very high concentration"
            score += points
            triggered_rules.append({"field": "top_holder_percent", "value": top_pct, "points": points, "severity": severity, "reason": reason})
            reasons.append(reason)
        elif top_pct >= 20:
            points, severity = 10, "Medium"
            reason = f"Top holder controls {top_pct:.0f}% of circulating supply — elevated concentration"
            score += points
            triggered_rules.append({"field": "top_holder_percent", "value": top_pct, "points": points, "severity": severity, "reason": reason})
            reasons.append(reason)
        else:
            not_triggered_rules.append({"field": "top_holder_percent", "value": top_pct, "reason": "No concerning holder concentration detected"})

    # Insider (owner/creator) concentration — separate from general holder concentration
    insider_pct = normalized.get("insider_percent")
    if insider_pct is not None:
        if insider_pct >= 20:
            points, severity = 15, "High"
            reason = f"Owner/creator wallet controls {insider_pct:.0f}% of supply directly"
            score += points
            triggered_rules.append({"field": "insider_percent", "value": insider_pct, "points": points, "severity": severity, "reason": reason})
            reasons.append(reason)
        else:
            not_triggered_rules.append({"field": "insider_percent", "value": insider_pct, "reason": "Owner/creator does not hold a concerning share of supply"})

    # Liquidity concentration/fragmentation — replaces the old binary "is any LP locked" check
    top_lp_pct = normalized.get("top_lp_holder_percent")
    lp_count = normalized.get("lp_position_count")
    if top_lp_pct is not None and lp_count is not None:
        if lp_count <= 2 and top_lp_pct >= 60:
            points, severity = 25, "Critical"
            reason = f"Liquidity is concentrated in {lp_count} position(s) — a single party could likely remove it"
            score += points
            triggered_rules.append({"field": "top_lp_holder_percent", "value": top_lp_pct, "points": points, "severity": severity, "reason": reason})
            reasons.append(reason)
        else:
            not_triggered_rules.append({
                "field": "top_lp_holder_percent", "value": top_lp_pct,
                "reason": f"Liquidity is fragmented across {lp_count} independent position(s) — no single party controls exit liquidity",
            })

    # Economic viability — absolute on-chain liquidity depth and recent trading
    # activity. This is the "the pool is effectively empty" signal that was
    # present in the raw provider data (per-pool tvl / volume) but never reached
    # the score before: concentration told you a single party COULD pull
    # liquidity, but not that there was almost none left to pull, or that nobody
    # is trading. A token can be contract-clean yet economically dead (unsellable
    # in practice, extreme slippage). Thresholds are intentionally coarse
    # buckets, not precise cutoffs — they express "trivial / thin / shallow"
    # liquidity, and we only score what the provider actually returned.
    #
    # total_liquidity_usd: absent (None) when the provider gave no pool TVL data
    # at all → skip silently (missing != zero). A real 0.0 (pools exist but hold
    # nothing) is a genuine, scoreable signal and is NOT skipped.
    total_liq = normalized.get("total_liquidity_usd")
    if total_liq is not None:
        if total_liq < 1_000:
            points, severity = 25, "High"
            reason = f"Effectively no liquidity — only ${total_liq:,.2f} across all known pools; the token is likely unsellable in any meaningful size"
        elif total_liq < 50_000:
            points, severity = 10, "Medium"
            reason = f"Shallow liquidity (~${total_liq:,.0f}) — larger trades will move the price significantly and may be hard to exit"
        else:
            points = 0
            not_triggered_rules.append({
                "field": "total_liquidity_usd", "value": total_liq,
                "reason": f"Adequate on-chain liquidity (~${total_liq:,.0f} across known pools)",
            })
        if points:
            score += points
            triggered_rules.append({"field": "total_liquidity_usd", "value": total_liq, "points": points, "severity": severity, "reason": reason})
            reasons.append(reason)

    # total_volume_24h_usd: same missing-vs-zero rule. Zero 24h volume on a token
    # that HAS pools is a real "no live market / abandoned" signal; combined with
    # thin TVL above it's the classic dead-token profile. Scored Medium, not
    # High — inactivity alone isn't proof of a trap, and the illiquidity rule
    # above already carries the weight when both are true.
    total_vol = normalized.get("total_volume_24h_usd")
    if total_vol is not None:
        if total_vol <= 0:
            points, severity = 10, "Medium"
            reason = "No recorded trading volume in the last 24h — the market for this token appears inactive or abandoned"
            score += points
            triggered_rules.append({"field": "total_volume_24h_usd", "value": total_vol, "points": points, "severity": severity, "reason": reason})
            reasons.append(reason)
        else:
            not_triggered_rules.append({
                "field": "total_volume_24h_usd", "value": total_vol,
                "reason": f"Active trading market (~${total_vol:,.0f} traded in the last 24h)",
            })

    # Positive signal — does not subtract points, but surfaced to the AI/response as reassurance
    if normalized.get("trust_list") is True:
        positive_signals.append("Token appears on GoPlus's trusted token list")

    is_critical_combo = False
    for combo_fields, combo_reason in CRITICAL_COMBOS:
        if combo_fields.issubset(triggered_field_names):
            is_critical_combo = True
            if combo_reason not in reasons:
                reasons.insert(0, combo_reason)

    score = min(score, 100)

    # ---- Risk level: the max of the numeric band and the severity floor ----
    # Two independent views of the same findings must agree on the headline:
    #   1. numeric band — the point total (breadth/accumulation of risk);
    #   2. severity floor — the single most severe finding (depth of the worst
    #      thing found), which the point total can under-weight.
    # We take whichever is HIGHER so a serious lone flag is never buried by a low
    # score, and a high score is never masked by individually-mild flags.
    numeric_level = "High" if score >= 70 else "Medium" if score >= 35 else "Low"

    severity_floor = "Low"
    critical_count = 0
    for rule in triggered_rules:
        sev = rule.get("severity", "Low")
        severity_floor = _max_level(severity_floor, SEVERITY_FLOOR.get(sev, "Low"))
        if sev == "Critical":
            critical_count += 1

    level = _max_level(numeric_level, severity_floor)

    # A named combo, OR any two independent Critical-severity findings, is the
    # top tier — consistent with the pre-existing combo behaviour, now general.
    if is_critical_combo or critical_count >= 2:
        level = "Critical"
        score = max(score, MULTI_CRITICAL_MIN_SCORE)

    known = normalized.get("_known_signals", 0)
    total = normalized.get("_total_signals", 1)
    confidence = round(known / total, 2) if total else 0.0

    # Highest severity actually observed — surfaced so the explanation layer can
    # lead with the worst finding instead of restating the score.
    present = {r.get("severity", "Low") for r in triggered_rules}
    max_severity = next(
        (sev for sev in ("Critical", "High", "Medium", "Low", "Informational") if sev in present),
        "None",
    )

    # Compact, structured economic context for the explanation layer (and any
    # downstream consumer) — None-safe, only the keys we actually resolved.
    economic_context = {
        k: normalized.get(k)
        for k in ("total_liquidity_usd", "total_volume_24h_usd")
        if normalized.get(k) is not None
    }

    return {
        "score": score,
        "risk_level": level,
        "max_severity": max_severity,
        "economic_context": economic_context,
        "reasons": reasons,
        "positive_signals": positive_signals,
        "triggered_rules": triggered_rules,
        "not_triggered_rules": not_triggered_rules,
        "confidence": confidence,
        "known_signals": known,
        "total_signals": total,
    }
