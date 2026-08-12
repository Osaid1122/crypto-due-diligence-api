"""
Regression tests for burn/incinerator exclusion in app/services/solana_normalizer.py.

Mirrors tests/test_normalizer.py for the EVM side. Two jobs:
  1. Prove the Solana incinerator (1nc1nerator1111...) is excluded from holder
     concentration, exactly as EVM excludes 0x000...dead / the zero address.
  2. Prove the real fixtures (SOLANA_USDC / SOLANA_TOES) are unaffected — neither
     contains an incinerator holder, so exclusion is a no-op on observed data and
     introduces no regression.

base58 is CASE-SENSITIVE: the burn address must match verbatim and must NOT be
lowercased. A case-mangled address is a *different* wallet and must still count.
"""

from app.services.scoring import score_token
from app.services.solana_normalizer import (
    SOLANA_BURN_ADDRESSES,
    normalize_solana,
)
from tests.fixtures.real_solana_samples import SOLANA_TOES, SOLANA_USDC

INCINERATOR = "1nc1nerator11111111111111111111111111111111"


def _rule(rules, field):
    return next((r for r in rules if r["field"] == field), None)


# ---------------------------------------------------------------------------
# Incinerator exclusion from holder concentration.
# ---------------------------------------------------------------------------

def test_incinerator_is_a_known_burn_address():
    # Guard against the constant being renamed/emptied — the exclusion below is
    # meaningless if the incinerator isn't actually in the set.
    assert INCINERATOR in SOLANA_BURN_ADDRESSES


def test_incinerator_holder_excluded_from_concentration():
    raw = {
        "holders": [
            {"account": INCINERATOR, "percent": "0.90", "is_locked": 0},
            {"account": "So11111111111111111111111111111111111111112", "percent": "0.07", "is_locked": 0},
        ]
    }
    # Incinerator holds 90% of burned supply — the top REAL holder is 7%.
    assert round(normalize_solana(raw)["top_holder_percent"], 2) == 7.0


def test_burned_token_is_not_flagged_as_concentrated_through_scoring():
    # normalize -> score_token: a token whose supply was burned to the
    # incinerator must not trigger the holder-concentration rule.
    raw = {
        "holders": [
            {"account": INCINERATOR, "percent": "0.95", "is_locked": 0},
            {"account": "So11111111111111111111111111111111111111112", "percent": "0.02", "is_locked": 0},
        ]
    }
    result = score_token(normalize_solana(raw))
    assert _rule(result["triggered_rules"], "top_holder_percent") is None


def test_incinerator_match_is_case_sensitive():
    # base58 is case-sensitive: a case-mangled "incinerator" is a DIFFERENT
    # address and must still be counted as a real holder.
    mangled = INCINERATOR.upper()  # not a valid burn address
    raw = {
        "holders": [
            {"account": mangled, "percent": "0.80", "is_locked": 0},
            {"account": "So11111111111111111111111111111111111111112", "percent": "0.01", "is_locked": 0},
        ]
    }
    # The mangled address is NOT excluded -> it is the top holder at 80%.
    assert round(normalize_solana(raw)["top_holder_percent"], 2) == 80.0


def test_only_incinerator_holder_yields_no_concentration():
    raw = {"holders": [{"account": INCINERATOR, "percent": "1.0", "is_locked": 0}]}
    assert normalize_solana(raw)["top_holder_percent"] is None


# ---------------------------------------------------------------------------
# Real fixtures are unaffected (no incinerator holder present -> no-op).
# ---------------------------------------------------------------------------

def test_solana_usdc_top_holder_unchanged():
    # USDC's real snapshot has no incinerator holder — top holder stays 10.54%.
    n = normalize_solana(SOLANA_USDC)
    assert round(n["top_holder_percent"], 2) == 10.54


def test_solana_usdc_still_scores_low():
    result = score_token(normalize_solana(SOLANA_USDC))
    assert result["risk_level"] == "Low"


def test_solana_toes_top_holder_unchanged():
    # TOES's real holders (~2.4% each) contain no incinerator — top stays ~2.47%.
    n = normalize_solana(SOLANA_TOES)
    assert round(n["top_holder_percent"], 2) == 2.47


def test_solana_toes_still_scores_high():
    # The economic-death + severity-floor behaviour these fixtures guard must be
    # untouched by the burn-exclusion change.
    result = score_token(normalize_solana(SOLANA_TOES))
    assert result["risk_level"] == "High"
