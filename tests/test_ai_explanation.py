"""
Tests for the templated (keyless / AI-outage) explanation synthesizer in
app/services/ai.py. This path is what the PUBLIC service actually returns
whenever OPENAI_API_KEY is unset, so it must produce a genuinely useful verdict
— lead with the worst finding, add economic context, credit clean authorities,
flag low confidence — not just restate the score.

The live OpenAI path is intentionally not called here (no network in tests); it
is exercised for its failure/CORS behaviour in test_cors_on_ai_failure.py.
"""

from app.services import scoring
from app.services.ai import build_templated_explanation
from app.services.solana_normalizer import normalize_solana
from tests.fixtures.real_solana_samples import SOLANA_TOES


def _explain(normalized, name, symbol):
    score_data = scoring.score_token(normalized)
    return build_templated_explanation(name, symbol, score_data), score_data


def test_summary_leads_with_dominant_finding_not_just_score():
    explanation, _ = _explain(normalize_solana(SOLANA_TOES), "TOES", "TOESCOIN")
    summary = explanation["summary"].lower()
    # The worst finding (liquidity) must be named, not merely a number.
    assert "liquid" in summary
    # And the practical economic read-through must be present.
    assert "unsellable" in summary or "sell" in summary or "abandoned" in summary or "inactive" in summary


def test_summary_flags_score_vs_severity_tension():
    # A High-severity finding under a non-High level should be called out.
    score_data = scoring.score_token({"total_liquidity_usd": 12.51})  # High severity, Medium level
    explanation = build_templated_explanation("X", "X", score_data)
    assert score_data["risk_level"] == "Medium" and score_data["max_severity"] == "High"
    assert "severity" in explanation["summary"].lower()


def test_summary_credits_clean_authorities_when_present():
    explanation, _ = _explain(normalize_solana(SOLANA_TOES), "TOES", "TOESCOIN")
    assert "positive side" in explanation["summary"].lower()


def test_low_confidence_is_called_out():
    score_data = {
        "score": 10, "risk_level": "Low", "max_severity": "Informational",
        "confidence": 0.30, "reasons": [], "positive_signals": [],
        "not_triggered_rules": [], "economic_context": {},
    }
    explanation = build_templated_explanation("Tok", "TK", score_data)
    assert "limited" in explanation["summary"].lower() or "partial" in explanation["summary"].lower()


def test_recommended_checks_prioritize_liquidity_when_thin():
    explanation, _ = _explain(normalize_solana(SOLANA_TOES), "TOES", "TOESCOIN")
    joined = " ".join(explanation["recommended_checks"]).lower()
    assert "liquid" in joined or "test sell" in joined


def test_score_substring_preserved_for_regression_contract():
    # Callers/tests rely on the literal 'scored <N>/100' substring.
    score_data = {
        "score": 18, "risk_level": "Low", "max_severity": "None",
        "confidence": 0.92, "reasons": [], "positive_signals": [],
        "not_triggered_rules": [], "economic_context": {},
    }
    explanation = build_templated_explanation("USD Coin", "USDC", score_data)
    assert "scored 18/100" in explanation["summary"]


def test_top_concerns_capped_at_three():
    score_data = {
        "score": 80, "risk_level": "High", "max_severity": "High", "confidence": 0.9,
        "reasons": ["a", "b", "c", "d", "e"], "positive_signals": [],
        "not_triggered_rules": [], "economic_context": {},
    }
    explanation = build_templated_explanation("T", "T", score_data)
    assert len(explanation["top_concerns"]) == 3
    assert len(explanation["recommended_checks"]) <= 3
