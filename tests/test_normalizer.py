"""
Regression tests for app/services/normalizer.py (the EVM normalizer).

Two jobs:
  1. Actually exercise the real GoPlus fixtures (USDC/LINK/UNI) end-to-end
     through normalize -> score_token, which nothing did before — this is the
     module the production-readiness audit found had zero coverage.
  2. Lock in burn-address exclusion, including the canonical zero address
     (0x000...000). A malformed 38-char zero-address literal previously failed
     to match real zero-address holders, so burned supply inflated holder
     concentration; these tests fail on that bug and pass once it's fixed.
"""

from app.services.normalizer import normalize
from app.services.scoring import score_token
from tests.fixtures.real_goplus_samples import LINK, UNI, USDC

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
DEAD_ADDRESS = "0x000000000000000000000000000000000000dead"


def _rule(rules, field):
    return next((r for r in rules if r["field"] == field), None)


# ---------------------------------------------------------------------------
# Burn / zero address exclusion from holder concentration.
# ---------------------------------------------------------------------------

def test_zero_address_holder_excluded_from_concentration():
    raw = {
        "holders": [
            {"address": ZERO_ADDRESS, "percent": "0.90", "is_locked": 0},
            {"address": "0x1111111111111111111111111111111111111111", "percent": "0.05", "is_locked": 0},
        ]
    }
    # The zero address holds 90% but is a burn sink — the top REAL holder is 5%.
    assert round(normalize(raw)["top_holder_percent"], 2) == 5.0


def test_dead_address_holder_excluded_from_concentration():
    raw = {
        "holders": [
            {"address": DEAD_ADDRESS, "percent": "0.80", "is_locked": 0},
            {"address": "0x2222222222222222222222222222222222222222", "percent": "0.04", "is_locked": 0},
        ]
    }
    assert round(normalize(raw)["top_holder_percent"], 2) == 4.0


def test_burn_address_match_is_case_insensitive():
    raw = {
        "holders": [
            {"address": DEAD_ADDRESS.upper().replace("0X", "0x"), "percent": "0.70", "is_locked": 0},
            {"address": "0x3333333333333333333333333333333333333333", "percent": "0.06", "is_locked": 0},
        ]
    }
    assert round(normalize(raw)["top_holder_percent"], 2) == 6.0


def test_zero_address_not_flagged_as_concentration_through_scoring():
    # normalize -> score_token: a token whose only large "holder" is the zero
    # burn address must not trigger the holder-concentration rule.
    raw = {
        "is_honeypot": "0",
        "holders": [
            {"address": ZERO_ADDRESS, "percent": "0.90", "is_locked": 0},
            {"address": "0x4444444444444444444444444444444444444444", "percent": "0.01", "is_locked": 0},
        ],
    }
    result = score_token(normalize(raw))
    assert _rule(result["triggered_rules"], "top_holder_percent") is None


def test_token_burned_to_zero_address_is_not_high_concentration_risk():
    # End-to-end: without the fix this token would look ~90% concentrated (High)
    # purely because supply was burned to 0x000...000.
    raw = {
        "is_honeypot": "0",
        "holders": [
            {"address": ZERO_ADDRESS, "percent": "0.92", "is_locked": 0},
            {"address": "0x5555555555555555555555555555555555555555", "percent": "0.03", "is_locked": 0},
            {"address": "0x6666666666666666666666666666666666666666", "percent": "0.02", "is_locked": 0},
        ],
    }
    result = score_token(normalize(raw))
    conc = _rule(result["triggered_rules"], "top_holder_percent")
    assert conc is None


# ---------------------------------------------------------------------------
# Real fixtures exercised end to end (USDC / LINK / UNI).
# ---------------------------------------------------------------------------

def test_usdc_fixture_normalizes_as_expected():
    n = normalize(USDC)
    assert n["is_honeypot"] is False
    assert n["is_open_source"] is True
    assert n["is_proxy"] is True
    assert n["trust_list"] is True
    # Top real holder ~8.66%; no burn/locked holders in this snapshot.
    assert round(n["top_holder_percent"], 2) == 8.66


def test_usdc_absent_fields_are_none_not_false():
    # Missing != false: USDC's payload has no is_mintable/hidden_owner at all.
    n = normalize(USDC)
    assert n["is_mintable"] is None
    assert n["hidden_owner"] is None
    assert n["cannot_sell_all"] is None


def test_usdc_scores_low():
    result = score_token(normalize(USDC))
    assert result["risk_level"] == "Low"


def test_link_fragmented_lp_is_not_flagged():
    n = normalize(LINK)
    # 10 distinct LP positions — fragmented liquidity, not a single-party exit.
    assert n["lp_position_count"] == 10
    result = score_token(n)
    assert _rule(result["triggered_rules"], "top_lp_holder_percent") is None
    assert round(n["top_holder_percent"], 2) == 5.5


def test_uni_dead_holder_excluded_and_owner_is_top():
    n = normalize(UNI)
    # UNI's holders include 0x...dead (10.69%, locked) — excluded — so the top
    # real holder is the owner wallet at ~27.21%.
    assert round(n["top_holder_percent"], 2) == 27.21


def test_all_real_fixtures_score_without_error():
    for raw in (USDC, LINK, UNI):
        result = score_token(normalize(raw))
        assert result["risk_level"] in ("Low", "Medium", "High", "Critical")
        assert 0 <= result["score"] <= 100
