from __future__ import annotations

from typing import Any


def is_numeric_risk_score(value: Any) -> bool:
    """True for real analysis scores, including zero, but never for None/bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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
        level = "Low"
    elif score >= 60:
        level = "Medium"
    elif score >= 40:
        level = "High"
    else:
        level = "Critical"

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
