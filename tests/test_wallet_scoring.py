"""
Tests for the wallet/portfolio aggregation in app/services/wallet/scoring.py.

The portfolio score is INVERTED relative to the token score (here higher =
safer). The behaviour these tests lock in is the portfolio-level severity floor:
a single dangerous holding must NOT be averaged away by many clean ones — the
same principle scoring.py enforces at the token level. Concretely:

  * one High-risk asset   -> portfolio at least Medium
  * one Critical asset     -> portfolio at least High
  * two or more Criticals  -> portfolio Critical

and crucially the numeric (inverted) score is pulled into the floored band, so a
consumer that re-derives the band from the number cannot silently restore "Low".
The floor only ever LIFTS severity — a genuinely bad average is never dragged
back down by it — and the empty / all-unscored behaviours are unchanged.
"""

from app.services.wallet.scoring import build_portfolio_score


def _asset(risk_score, risk_level, has_audit=False):
    """Minimal shape of an analyzed asset as produced by wallet/analyzer.py."""
    return {"risk_score": risk_score, "risk_level": risk_level, "has_audit": has_audit}


# ---------------------------------------------------------------------------
# Baseline: a clean portfolio stays Low.
# ---------------------------------------------------------------------------

def test_all_clean_portfolio_is_low():
    result = build_portfolio_score([_asset(5, "Low") for _ in range(5)])
    assert result["risk_level"] == "Low"
    assert result["score"] >= 80


# ---------------------------------------------------------------------------
# Severity floor — the core fix. A lone dangerous holding is not buried.
# ---------------------------------------------------------------------------

def test_one_high_asset_floors_portfolio_to_at_least_medium():
    # 1 High-risk holding + 9 clean ones. Raw average is ~4 (would be "Low"/96),
    # but the worst holding must floor the portfolio to at least Medium.
    assets = [_asset(40, "High")] + [_asset(0, "Low") for _ in range(9)]
    result = build_portfolio_score(assets)
    assert result["risk_level"] == "Medium"
    assert result["score"] < 80  # cannot remain in the Low band
    # The diagnostic mean is still reported honestly (not clamped).
    assert result["detail_metrics"]["average_token_risk"] == 4


def test_one_critical_asset_floors_portfolio_to_at_least_high():
    assets = [_asset(90, "Critical")] + [_asset(0, "Low") for _ in range(9)]
    result = build_portfolio_score(assets)
    assert result["risk_level"] == "High"
    assert result["score"] < 60  # re-deriving the band from the score -> High


def test_single_dangerous_holding_is_not_buried_by_averaging():
    # The explicit "cannot be averaged away" case: 1 dangerous holding diluted
    # by 19 clean ones. This is exactly the trap the token engine already fixed.
    assets = [_asset(40, "High")] + [_asset(0, "Low") for _ in range(19)]
    result = build_portfolio_score(assets)
    assert result["risk_level"] != "Low"
    assert result["score"] < 80


def test_two_critical_assets_escalate_portfolio_to_critical():
    assets = [_asset(90, "Critical"), _asset(95, "Critical")] + [_asset(0, "Low") for _ in range(8)]
    result = build_portfolio_score(assets)
    assert result["risk_level"] == "Critical"
    assert result["score"] < 40


def test_multiple_high_assets_floor_to_medium():
    assets = [_asset(45, "High") for _ in range(3)] + [_asset(0, "Low") for _ in range(7)]
    result = build_portfolio_score(assets)
    assert result["risk_level"] == "Medium"


# ---------------------------------------------------------------------------
# The floor only lifts — a genuinely bad average is never dragged back down.
# ---------------------------------------------------------------------------

def test_numeric_band_is_preserved_when_average_is_genuinely_bad():
    # Ten high-risk holdings: the average alone yields Critical (score 25).
    # The High->Medium floor must NOT lower it; max(Critical, Medium) = Critical.
    assets = [_asset(75, "High") for _ in range(10)]
    result = build_portfolio_score(assets)
    assert result["risk_level"] == "Critical"


def test_floor_never_downgrades_the_numeric_level():
    # Property check: the returned band is always at least the raw numeric band.
    order = ["Low", "Medium", "High", "Critical"]
    assets = [_asset(60, "High"), _asset(55, "High"), _asset(10, "Low")]
    result = build_portfolio_score(assets)
    avg = sum(a["risk_score"] for a in assets) / len(assets)
    raw_score = round(100 - avg)
    numeric = "Low" if raw_score >= 80 else "Medium" if raw_score >= 60 else "High" if raw_score >= 40 else "Critical"
    assert order.index(result["risk_level"]) >= order.index(numeric)


# ---------------------------------------------------------------------------
# Unscored / native assets never contribute to the floor or the average.
# ---------------------------------------------------------------------------

def test_unscored_assets_do_not_affect_floor():
    assets = [
        _asset(5, "Low"),
        _asset(3, "Low"),
        {"risk_score": None, "risk_level": "Unscored"},  # native/unavailable
    ]
    result = build_portfolio_score(assets)
    assert result["risk_level"] == "Low"
    assert result["score"] >= 80


# ---------------------------------------------------------------------------
# Empty / invalid portfolio behaviour must be preserved exactly.
# ---------------------------------------------------------------------------

def test_empty_portfolio_preserves_unknown_behaviour():
    result = build_portfolio_score([])
    assert result["score"] == 0
    assert result["risk_level"] == "Unknown"


def test_all_unscored_portfolio_preserves_unknown_behaviour():
    assets = [
        {"risk_score": None, "risk_level": "Unscored"},
        {"risk_score": None, "risk_level": "Unknown"},
    ]
    result = build_portfolio_score(assets)
    assert result["score"] is None
    assert result["risk_level"] == "Unknown"


# ---------------------------------------------------------------------------
# The floor explains itself in the report when it lifts the band.
# ---------------------------------------------------------------------------

def test_floor_adds_explaining_recommendation():
    assets = [_asset(90, "Critical")] + [_asset(0, "Low") for _ in range(9)]
    result = build_portfolio_score(assets)
    assert any("worst holding" in rec for rec in result["recommendations"])


def test_no_floor_recommendation_for_clean_portfolio():
    result = build_portfolio_score([_asset(5, "Low") for _ in range(5)])
    assert not any("worst holding" in rec for rec in result["recommendations"])
