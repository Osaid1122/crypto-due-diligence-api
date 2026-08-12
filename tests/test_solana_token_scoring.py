"""
End-to-end tests for the Solana token pipeline: real GoPlus sample ->
normalize_solana -> score_token. These lock in the two fixes that the raw
score-only engine got wrong on real data:

  * TOES (TOESCOIN): contract authorities all clean, but liquidity is both
    concentrated AND economically dead ($12.51 TVL, $0 volume). Must NOT be
    "Low" — the severity floor + economic signals push it to "High".
  * USDC on Solana: deep, fragmented liquidity and no economic red flags — must
    stay "Low", and crucially its ABSENT volume field must not be read as
    "zero volume" (missing != zero).
"""

from app.services.scoring import score_token
from app.services.solana_normalizer import normalize_solana
from tests.fixtures.real_solana_samples import SOLANA_TOES, SOLANA_USDC


def _rule(rules, field):
    return next((r for r in rules if r["field"] == field), None)


# ---------------------------------------------------------------------------
# TOES — the dead-but-clean token the original engine mislabelled as Low.
# ---------------------------------------------------------------------------

def test_toes_normalizes_absolute_economic_signals():
    n = normalize_solana(SOLANA_TOES)
    assert n["total_liquidity_usd"] == 12.51          # 12.51 + 0
    assert n["total_volume_24h_usd"] == 0.0           # reported zero, not missing
    # Concentration share across the two pools is ~100%.
    assert round(n["top_lp_holder_percent"], 2) == 100.0
    assert n["lp_position_count"] == 2


def test_toes_is_not_low_risk():
    result = score_token(normalize_solana(SOLANA_TOES))
    assert result["risk_level"] == "High"
    assert result["max_severity"] == "Critical"


def test_toes_flags_dead_liquidity_and_no_volume():
    result = score_token(normalize_solana(SOLANA_TOES))
    liq = _rule(result["triggered_rules"], "total_liquidity_usd")
    vol = _rule(result["triggered_rules"], "total_volume_24h_usd")
    conc = _rule(result["triggered_rules"], "top_lp_holder_percent")
    assert liq is not None and liq["severity"] == "High"
    assert vol is not None and vol["severity"] == "Medium"
    assert conc is not None and conc["severity"] == "Critical"


def test_toes_credits_clean_authorities():
    # Mint/freeze revoked, not closable etc. must still be reported as clean,
    # so the verdict is "dangerous economically, clean on control" — not a
    # blanket alarm.
    result = score_token(normalize_solana(SOLANA_TOES))
    clean = {r["field"] for r in result["not_triggered_rules"]}
    assert "has_mint_authority" in clean
    assert "has_freeze_authority" in clean
    assert "closable" in clean


# ---------------------------------------------------------------------------
# USDC on Solana — the deep-liquidity control case. Must not regress to a
# false economic flag when the provider omits volume data.
# ---------------------------------------------------------------------------

def test_usdc_solana_stays_low_risk():
    result = score_token(normalize_solana(SOLANA_USDC))
    assert result["risk_level"] == "Low"


def test_usdc_solana_missing_volume_is_not_scored_as_zero():
    n = normalize_solana(SOLANA_USDC)
    # No dex pool in the real USDC sample carries a day.volume key.
    assert n["total_volume_24h_usd"] is None
    result = score_token(n)
    # ...so the zero-volume rule must NOT fire on the most-traded SPL stablecoin.
    assert _rule(result["triggered_rules"], "total_volume_24h_usd") is None


def test_usdc_solana_deep_liquidity_is_clean():
    result = score_token(normalize_solana(SOLANA_USDC))
    assert _rule(result["triggered_rules"], "total_liquidity_usd") is None
    assert _rule(result["not_triggered_rules"], "total_liquidity_usd") is not None
