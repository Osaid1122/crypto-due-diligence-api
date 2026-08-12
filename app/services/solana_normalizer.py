"""
Normalizes raw GoPlus Solana Token Security data into the SAME normalized
signal shape scoring.py already understands for EVM tokens. Where a Solana
concept's risk profile genuinely matches its EVM counterpart (trust list,
holder concentration, liquidity concentration), the same field names are
reused so scoring.py's existing rules apply with zero changes. Where real
data showed the risk profile differs (mint/freeze authority — see below),
Solana gets its own field name and its own honestly-tuned weight instead of
inheriting an EVM weight calibrated for a different chain's risk pattern.
Solana-only concepts with no EVM equivalent get entirely new field names.
EVM tokens never populate any Solana-specific key, so those keys stay
absent (None) for EVM and never affect EVM scoring or confidence.

Every field name and shape below is verified against a real, live,
authenticated GoPlus response for USDC on Solana (2026-07-19) — not assumed
from documentation, which itself proved incomplete: `dex`, `holder_count`,
`lp_holders`, and `creators` are all real, populated fields absent from
GoPlus's own docs page; conversely, the docs' `creator` field doesn't
exist — the real field is `creators` (plural, array).
"""

from typing import Any, Optional

# Fields sharing the {authority: [...], status: "0"|"1"} shape — confirmed
# identical across all of them in the real USDC response.
STATUS_SHAPE_FIELDS = [
    "mintable", "freezable", "metadata_mutable", "closable",
    "balance_mutable_authority",
]

TRUE_VALUES = {"1", 1, True}
FALSE_VALUES = {"0", 0, False}

# Canonical Solana incinerator — the well-known, documented burn sink that
# `solana burn`/account-closing routes tokens to. This is the direct analog of
# EVM's 0x000...dead / zero address handled in normalizer.py: supply parked here
# is destroyed, not circulating, so it must be excluded from holder-concentration
# math or a token whose supply was burned looks artificially concentrated.
# NOT invented — it is a fixed, publicly known address. base58 is CASE-SENSITIVE,
# so (unlike the EVM hex addresses) it must be matched verbatim, never lowercased.
SOLANA_BURN_ADDRESSES = {
    "1nc1nerator11111111111111111111111111111111",
}


def _status_bool(raw: dict, field: str) -> Optional[bool]:
    entry = raw.get(field)
    if not isinstance(entry, dict) or "status" not in entry:
        return None
    val = entry.get("status")
    if val in TRUE_VALUES:
        return True
    if val in FALSE_VALUES:
        return False
    return None


def _real_holders(raw: dict) -> list[dict]:
    """Holders with the incinerator/burn sink excluded — mirrors the EVM
    normalizer's _real_holders. Burned supply is destroyed, not circulating, so
    it must not count toward concentration. Matched verbatim on the `account`
    field: base58 is case-sensitive and must NOT be lowercased (unlike EVM hex)."""
    holders = raw.get("holders") or []
    return [h for h in holders if h.get("account") not in SOLANA_BURN_ADDRESSES]


def _top_holder_percent(raw: dict) -> Optional[float]:
    holders = _real_holders(raw)
    if not holders:
        return None
    try:
        # Same fractional (0-1) convention as EVM — confirmed against real
        # data: USDC's top holder shows percent "0.1054" = 10.54%.
        return max(float(h.get("percent", 0)) * 100 for h in holders)
    except (ValueError, TypeError):
        return None


def _liquidity_signal(raw: dict) -> tuple[Optional[float], Optional[int]]:
    """
    Returns (top_pool_tvl_share_percent, pool_count).

    NOTE on a real data gap: `lp_holders` is a genuine field in the schema
    but was an empty array for our one live sample (USDC) — its populated
    shape is NOT yet verified against real data, so it is deliberately not
    parsed here rather than guessed at. `dex` returned rich, real, populated
    data instead (per-pool TVL across Orca and Raydium for USDC), so
    liquidity concentration is derived from TVL share across pools —
    a reasonable, data-grounded proxy for the same underlying risk
    (liquidity concentrated somewhere a single party could pull it), though
    it measures pool-level concentration rather than LP-token-holder-level
    concentration the way the EVM version does. Worth revisiting once a
    real example with populated `lp_holders` is available.
    """
    dex_pools = raw.get("dex") or []
    if not dex_pools:
        return None, None
    try:
        tvls = [float(p.get("tvl", 0)) for p in dex_pools if p.get("tvl") is not None]
        total_tvl = sum(tvls)
        if total_tvl <= 0:
            return None, len(dex_pools)
        top_share = (max(tvls) / total_tvl) * 100
        return top_share, len(dex_pools)
    except (ValueError, TypeError):
        return None, len(dex_pools)


def _economic_signal(raw: dict) -> tuple[Optional[float], Optional[int], Optional[float]]:
    """
    Returns (total_liquidity_usd, pool_count, total_volume_24h_usd) — absolute
    economic depth/activity, distinct from the concentration SHARE above.

    Verified against real data: each `dex[]` entry carries a string `tvl`
    (confirmed on USDC — Orca/Raydium pools) and a nested `day.volume`
    (confirmed on a real risky token captured 2026-08-08 — see
    tests/fixtures/real_solana_samples.py::SOLANA_TOES). This is the "the pool
    is effectively empty / nobody is trading" signal that concentration alone
    cannot express.

    Critical distinction (a repeatedly-learned lesson in this codebase — see
    normalizer.py): MISSING != ZERO.
      * total_liquidity_usd is None only when NO pool carried a tvl at all; a
        genuine 0.0 (pools exist but hold nothing) is returned as 0.0 and is a
        real, scoreable signal.
      * total_volume_24h_usd is None unless AT LEAST ONE pool actually reported
        a `day.volume` key. USDC's real sample has no volume field, so returning
        0.0 there would be a false "no trading" signal on the most-traded
        stablecoin on Solana. Only a present-but-zero volume is reported as 0.0.
    """
    dex_pools = raw.get("dex") or []
    if not dex_pools:
        return None, None, None

    tvls: list[float] = []
    volumes: list[float] = []
    volume_reported = False
    for p in dex_pools:
        tvl = p.get("tvl")
        if tvl is not None:
            try:
                tvls.append(float(tvl))
            except (ValueError, TypeError):
                pass
        day = p.get("day")
        if isinstance(day, dict) and day.get("volume") is not None:
            volume_reported = True
            try:
                volumes.append(float(day.get("volume")))
            except (ValueError, TypeError):
                pass

    total_tvl = sum(tvls) if tvls else None
    total_volume = sum(volumes) if volume_reported else None
    return total_tvl, len(dex_pools), total_volume


def normalize_solana(raw: dict) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    known_count = 0
    total_count = 0

    # ---- Shared concepts — reuse EVM's normalized field names so
    # scoring.py's existing rules apply without any modification ----

    total_count += 1
    # NOT reusing EVM's is_mintable field name/weight here — deliberately.
    # Real data (USDC on Solana) shows mint authority present on a
    # maximally-trusted token; on Solana this is closer to normal token
    # administration than an EVM-style abuse risk, so it gets its own
    # honestly-low weight (see scoring.py) rather than inheriting EVM's
    # is_mintable weight, which was tuned for a chain where persistent mint
    # access is a more meaningful red flag. Same category of correction
    # already applied to EVM's own is_proxy after seeing real USDC data.
    has_mint_authority = _status_bool(raw, "mintable")
    normalized["has_mint_authority"] = has_mint_authority
    if has_mint_authority is not None:
        known_count += 1

    total_count += 1
    # Same reasoning as above — not reused as EVM's is_blacklisted. Freeze
    # authority is conceptually the closest Solana analog to a blacklist
    # capability, but real data shows it present on trusted USDC too, so it
    # gets its own weight rather than EVM's.
    has_freeze_authority = _status_bool(raw, "freezable")
    normalized["has_freeze_authority"] = has_freeze_authority
    if has_freeze_authority is not None:
        known_count += 1

    total_count += 1
    trusted = raw.get("trusted_token")
    normalized["trust_list"] = (trusted in TRUE_VALUES) if trusted is not None else None
    if trusted is not None:
        known_count += 1

    total_count += 1
    top_holder_pct = _top_holder_percent(raw)
    normalized["top_holder_percent"] = top_holder_pct
    if top_holder_pct is not None:
        known_count += 1

    total_count += 1
    top_lp_pct, pool_count = _liquidity_signal(raw)
    normalized["top_lp_holder_percent"] = top_lp_pct
    normalized["lp_position_count"] = pool_count
    if top_lp_pct is not None:
        known_count += 1

    # ---- Economic depth/activity — absolute TVL and 24h volume, distinct from
    # the concentration SHARE above. Additive and None-safe: these keys are
    # never populated by the EVM normalizer, so they stay absent for EVM tokens
    # and never affect EVM scoring or confidence. total_liquidity_usd counts
    # toward confidence when any pool TVL was present; total_volume_24h_usd only
    # when at least one pool actually reported a volume (missing != zero — USDC's
    # real sample has no volume field and must not read as "no trading"). ----
    total_liq, _pool_count_econ, total_vol = _economic_signal(raw)

    total_count += 1
    normalized["total_liquidity_usd"] = total_liq
    if total_liq is not None:
        known_count += 1

    total_count += 1
    normalized["total_volume_24h_usd"] = total_vol
    if total_vol is not None:
        known_count += 1

    # is_open_source and is_proxy have no meaningful Solana equivalent —
    # most SPL tokens run on the shared, already-audited Token/Token-2022
    # program rather than custom per-token contract logic. Deliberately
    # left unset (None) rather than force-mapped, so they're correctly
    # excluded from confidence and never silently scored as true/false for
    # a concept that doesn't apply on this chain.

    # ---- Solana-only concepts — no EVM equivalent, new CHECKS entries in
    # scoring.py. Additive: these keys are never populated by the EVM
    # normalizer, so they're always None for EVM tokens and never affect
    # EVM scoring or confidence. ----

    total_count += 1
    is_closable = _status_bool(raw, "closable")
    normalized["closable"] = is_closable
    if is_closable is not None:
        known_count += 1

    total_count += 1
    balance_mutable = _status_bool(raw, "balance_mutable_authority")
    normalized["balance_mutable_authority"] = balance_mutable
    if balance_mutable is not None:
        known_count += 1

    total_count += 1
    metadata_mutable = _status_bool(raw, "metadata_mutable")
    normalized["metadata_mutable"] = metadata_mutable
    if metadata_mutable is not None:
        known_count += 1

    total_count += 1
    # transfer_hook is a list, not a {status} object — a different shape
    # from its siblings above, confirmed against real data (empty list for
    # USDC, which is a legacy SPL token, not Token-2022 — we don't yet have
    # a real example of a token that actually uses this feature).
    transfer_hook = raw.get("transfer_hook")
    has_transfer_hook = (len(transfer_hook) > 0) if isinstance(transfer_hook, list) else None
    normalized["has_transfer_hook"] = has_transfer_hook
    if has_transfer_hook is not None:
        known_count += 1

    normalized["_known_signals"] = known_count
    normalized["_total_signals"] = total_count

    metadata = raw.get("metadata") or {}
    normalized["token_name"] = metadata.get("name")
    normalized["token_symbol"] = metadata.get("symbol")

    # creators: a real field in the schema, but empty for our one live
    # sample — surfaced for display/technical_data only, not scored, since
    # we have no real example of its populated shape to safely design a
    # rule against (see project convention: don't invent mappings that
    # aren't backed by observed real data).
    normalized["creators"] = raw.get("creators") or []
    normalized["holder_count"] = raw.get("holder_count")

    return normalized
