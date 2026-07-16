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
]

CRITICAL_COMBOS: list[tuple[set, str]] = [
    ({"is_honeypot", "cannot_sell_all"}, "Token appears to trap funds — flagged as a honeypot AND unable to sell in full"),
    ({"is_honeypot", "is_blacklisted"}, "Token can both block specific wallets and trap funds entirely"),
    ({"is_proxy", "hidden_owner"}, "Upgradeable contract combined with a hidden owner — control can change with no visible accountability"),
    ({"is_proxy", "can_take_back_ownership"}, "Upgradeable contract combined with reclaimable ownership — high potential for rug pull via upgrade"),
]


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

    if is_critical_combo:
        level = "Critical"
        score = max(score, 90)
    elif score >= 70:
        level = "High"
    elif score >= 35:
        level = "Medium"
    else:
        level = "Low"

    known = normalized.get("_known_signals", 0)
    total = normalized.get("_total_signals", 1)
    confidence = round(known / total, 2) if total else 0.0

    return {
        "score": score,
        "risk_level": level,
        "reasons": reasons,
        "positive_signals": positive_signals,
        "triggered_rules": triggered_rules,
        "not_triggered_rules": not_triggered_rules,
        "confidence": confidence,
        "known_signals": known,
        "total_signals": total,
    }
