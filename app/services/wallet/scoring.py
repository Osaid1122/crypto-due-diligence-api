from __future__ import annotations

from typing import Any

from app.services.scoring import LEVELS, SEVERITY_FLOOR

# Highest safety score still consistent with each portfolio risk band. The
# portfolio score is INVERTED (higher = safer), so whenever the severity floor
# lifts the band above what the raw average implies, we also pull the numeric
# score down into that band's range. Otherwise a wallet could read "96 / High",
# and any consumer that re-derives the band from the number (the frontend does)
# would silently undo the floor. Mirrors bands below: Low>=80, Medium>=60,
# High>=40, Critical<40.
_LEVEL_SCORE_CEILING = {"Low": 100, "Medium": 79, "High": 59, "Critical": 39}


def is_numeric_risk_score(value: Any) -> bool:
    """True for real analysis scores, including zero, but never for None/bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _more_severe(a: str, b: str) -> str:
    """The higher-severity of two risk bands, per scoring.py's shared ladder."""
    return a if LEVELS.index(a) >= LEVELS.index(b) else b


def build_portfolio_score(assets: list[dict[str, Any]]) -> dict[str, Any]:
    # NOTE: this portfolio score is INVERTED relative to the token-level score in
    # app/services/scoring.py. Here, higher = safer (100 is a clean portfolio);
    # there, higher = riskier (100 is maximum detected token risk). The inversion
    # happens at `score = 100 - average` below, where `average` is the mean of the
    # token-level (higher = riskier) asset scores.
    if not assets:
        return {
            "score": 0,
            "risk_level": "Unknown",
            "risk_breakdown": [],
            "detail_metrics": {
                "average_token_risk": 0,
                "diversification": "Limited",
                "liquidity_quality": "Unknown",
                "audit_coverage": 0,
            },
            "recommendations": ["No live wallet assets were found, so no portfolio score was generated."],
        }

    # Do not turn an unavailable token-security lookup into a zero-risk
    # asset. Only assets with a real numeric analysis participate in the
    # canonical portfolio score.
    scored_assets = [item for item in assets if is_numeric_risk_score(item.get("risk_score"))]
    if not scored_assets:
        return {
            "score": None,
            "risk_level": "Unknown",
            "risk_breakdown": [],
            "detail_metrics": {"average_token_risk": None, "diversification": "Unknown", "liquidity_quality": "Unknown", "audit_coverage": 0},
            "recommendations": ["No eligible assets returned a live contract-security analysis."],
        }

    scores = [item["risk_score"] for item in scored_assets]
    average = sum(scores) / len(scores)
    score = int(round(100 - average))
    score = max(0, min(100, score))

    if score >= 80:
        numeric_level = "Low"
    elif score >= 60:
        numeric_level = "Medium"
    elif score >= 40:
        numeric_level = "High"
    else:
        numeric_level = "Critical"

    # ---- Severity floor: a single dangerous holding must not be averaged away
    # by many clean ones. This mirrors the token-level severity floor in
    # app/services/scoring.py, where a lone serious finding sets a minimum risk
    # level regardless of the point total. Here the "findings" are the per-asset
    # risk levels — which the token engine already severity-floored — so we reuse
    # the same SEVERITY_FLOOR ladder rather than re-deriving thresholds:
    #   one High-risk asset   -> portfolio at least Medium
    #   one Critical asset    -> portfolio at least High
    #   two or more Criticals -> portfolio Critical (mirrors scoring.py's
    #                            critical_count >= 2 escalation).
    # Only assets with a real numeric analysis (scored_assets) carry a canonical
    # risk_level, so unscored/native assets never contribute to the floor.
    worst_asset_level = "Low"
    critical_assets = 0
    for item in scored_assets:
        asset_level = item.get("risk_level")
        if asset_level not in LEVELS:
            continue
        worst_asset_level = _more_severe(worst_asset_level, asset_level)
        if asset_level == "Critical":
            critical_assets += 1

    level = _more_severe(numeric_level, SEVERITY_FLOOR.get(worst_asset_level, "Low"))
    if critical_assets >= 2:
        level = "Critical"

    # Keep the inverted score consistent with a floored-up band so the headline
    # number itself can't under-report the risk the band now reflects.
    score = min(score, _LEVEL_SCORE_CEILING[level])

    safe_assets = sum(1 for item in scored_assets if item["risk_score"] <= 30)
    medium_assets = sum(1 for item in scored_assets if 31 <= item["risk_score"] <= 70)
    high_assets = sum(1 for item in scored_assets if item["risk_score"] > 70)

    if len(scored_assets) >= 8 and safe_assets >= 5:
        diversification = "Good"
    elif len(scored_assets) >= 4:
        diversification = "Mixed"
    else:
        diversification = "Limited"

    if safe_assets >= max(2, len(scored_assets) // 2):
        liquidity_quality = "Excellent"
    elif medium_assets >= safe_assets:
        liquidity_quality = "Needs review"
    else:
        liquidity_quality = "Good"

    audit_coverage = round((sum(1 for item in scored_assets if item.get("has_audit")) / len(scored_assets)) * 100)

    risk_breakdown = [
        {"label": "Low risk", "value": safe_assets},
        {"label": "Medium risk", "value": medium_assets},
        {"label": "High risk", "value": high_assets},
    ]

    recommendations = [
        "Review the highest-risk assets in this wallet before interacting.",
        "Verify ownership concentration and approval permissions for each flagged token.",
    ]
    if high_assets:
        recommendations.append(f"Inspect {high_assets} high-risk asset(s) for concentrated holdings, proxy risk, or unlocked liquidity.")
    if level != numeric_level:
        recommendations.insert(
            0,
            f"At least one holding is individually {worst_asset_level.lower()} risk — the portfolio band reflects that "
            f"worst holding, not the average across all assets.",
        )

    return {
        "score": score,
        "risk_level": level,
        "risk_breakdown": risk_breakdown,
        "detail_metrics": {
            "average_token_risk": round(average),
            "diversification": diversification,
            "liquidity_quality": liquidity_quality,
            "audit_coverage": audit_coverage,
        },
        "recommendations": recommendations,
    }
