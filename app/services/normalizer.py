"""
Normalizes raw provider data (currently GoPlus) into a stable internal shape.

Field names below were verified against real GoPlus responses for USDC, LINK,
and UNI on 2026-07-10 (see tests/fixtures/real_goplus_samples.py) — not just docs.

Confirmed from real data:
- Fields genuinely go missing per-token (USDC has no is_mintable/lp_holders at all).
  Missing != false. Only score what's actually present.
- Burn addresses (0x000...dead) show up as real "holders" and must be excluded from
  concentration math, or a token like UNI looks artificially risky.
- lp_holders' individual is_locked flags are unreliable as a standalone signal —
  LINK has 10+ genuine LP positions, none locked, and it's one of the most liquid
  tokens in crypto. What actually matters is concentration: is liquidity fragmented
  across many independent LPs (healthy) or controlled by one or two (risky)?
"""

from typing import Any, Optional

EXPECTED_BOOL_FIELDS = [
    "is_honeypot",
    "is_mintable",
    "cannot_sell_all",
    "is_blacklisted",
    "hidden_owner",
    "can_take_back_ownership",
    "selfdestruct",
    "is_proxy",
    "trading_cooldown",
    "is_open_source",
]

TRUE_VALUES = {"1", 1, True, "true", "True", "yes"}
FALSE_VALUES = {"0", 0, False, "false", "False", "no"}

BURN_ADDRESSES = {
    "0x000000000000000000000000000000000000dead",
    # Canonical zero address (0x + 40 hex zeros) — the most common burn sink.
    # Must be the full 40-char form; a shorter literal silently fails to match
    # real zero-address holders and inflates concentration on burned supply.
    "0x0000000000000000000000000000000000000000",
}


def _present(raw: dict, key: str) -> bool:
    return key in raw and raw.get(key) is not None


def _as_bool(raw: dict, key: str) -> Optional[bool]:
    if not _present(raw, key):
        return None
    value = raw.get(key)
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    return None


def _as_float(raw: dict, key: str) -> Optional[float]:
    if not _present(raw, key):
        return None
    try:
        return float(raw.get(key))
    except (ValueError, TypeError):
        return None


def _real_holders(raw: dict) -> list[dict]:
    """Holders list with burn addresses and explicitly-locked (e.g. team/vesting
    lock) positions excluded — those aren't circulating concentration risk."""
    holders = raw.get("holders") or []
    return [
        h for h in holders
        if h.get("address", "").lower() not in BURN_ADDRESSES
        and str(h.get("is_locked", 0)) not in ("1", "True", "true")
    ]


def _top_holder_percent(raw: dict) -> Optional[float]:
    real = _real_holders(raw)
    if not real:
        return None
    try:
        return max(float(h.get("percent", 0)) * 100 for h in real)
    except (ValueError, TypeError):
        return None


def _lp_concentration(raw: dict) -> tuple[Optional[float], Optional[int]]:
    """Returns (top_lp_holder_percent, lp_position_count). None if no LP data at all.
    A high top-holder percentage across only 1-2 positions is the real red flag —
    fragmented liquidity across many independent LPs (regardless of individual
    is_locked flags) is a healthy sign, not a risk."""
    lp_holders = raw.get("lp_holders")
    if not lp_holders:
        return None, None
    try:
        top_pct = max(float(h.get("percent", 0)) * 100 for h in lp_holders)
        return top_pct, len(lp_holders)
    except (ValueError, TypeError):
        return None, len(lp_holders)


def normalize(raw: dict) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    known_count = 0
    total_count = 0

    for field in EXPECTED_BOOL_FIELDS:
        total_count += 1
        value = _as_bool(raw, field)
        normalized[field] = value
        if value is not None:
            known_count += 1

    total_count += 1
    top_pct = _top_holder_percent(raw)
    normalized["top_holder_percent"] = top_pct
    if top_pct is not None:
        known_count += 1

    total_count += 1
    top_lp_pct, lp_count = _lp_concentration(raw)
    normalized["top_lp_holder_percent"] = top_lp_pct
    normalized["lp_position_count"] = lp_count
    if top_lp_pct is not None:
        known_count += 1

    total_count += 1
    owner_pct = _as_float(raw, "owner_percent")
    creator_pct = _as_float(raw, "creator_percent")
    # both are fractional (0-1) like holders[].percent — take whichever is higher/known
    insider_pct = max([p for p in (owner_pct, creator_pct) if p is not None], default=None)
    if insider_pct is not None:
        insider_pct *= 100
        known_count += 1
    normalized["insider_percent"] = insider_pct

    total_count += 1
    trust_list = _as_bool(raw, "trust_list")
    normalized["trust_list"] = trust_list
    if trust_list is not None:
        known_count += 1

    normalized["_known_signals"] = known_count
    normalized["_total_signals"] = total_count
    normalized["token_name"] = raw.get("token_name")
    normalized["token_symbol"] = raw.get("token_symbol")

    return normalized
