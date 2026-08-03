"""
Tests for the deterministic token risk scoring engine (app/services/scoring.py).

Coverage:
  * every row in CHECKS — fires with correct points/severity when the field
    matches its trigger_value, and is absent from triggered_rules (and present
    in not_triggered_rules) when it doesn't;
  * all CRITICAL_COMBOS — score forced to >= 90 and level == "Critical" when
    both fields in a combo trigger;
  * the top_holder_percent / insider_percent / top_lp_holder_percent threshold
    branches, just above and below each cutoff;
  * confidence calculation with partial known_signals.

The CHECKS and CRITICAL_COMBOS tests are parametrized off the tables in the
module itself, so a new rule added to scoring.py is automatically exercised.
"""

import pytest

from app.services import scoring


def _find(rules: list[dict], field: str) -> dict | None:
    return next((rule for rule in rules if rule["field"] == field), None)


# ---------------------------------------------------------------------------
# CHECKS — one triggered + one not-triggered assertion per row.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field,trigger_value,points,severity,reason,clean_label", scoring.CHECKS)
def test_check_fires_when_field_matches_trigger(field, trigger_value, points, severity, reason, clean_label):
    result = scoring.score_token({field: trigger_value})

    rule = _find(result["triggered_rules"], field)
    assert rule is not None, f"{field} should appear in triggered_rules when it matches its trigger value"
    assert rule["points"] == points
    assert rule["severity"] == severity
    # A matched rule must not also be reported as not-triggered.
    assert _find(result["not_triggered_rules"], field) is None


@pytest.mark.parametrize("field,trigger_value,points,severity,reason,clean_label", scoring.CHECKS)
def test_check_absent_when_field_does_not_match(field, trigger_value, points, severity, reason, clean_label):
    # Every trigger_value in CHECKS is a boolean, so the opposite boolean is a
    # concrete non-triggering value (and importantly not None, which would be
    # skipped entirely rather than counted as "clean").
    non_trigger = not trigger_value
    result = scoring.score_token({field: non_trigger})

    assert _find(result["triggered_rules"], field) is None
    assert _find(result["not_triggered_rules"], field) is not None, (
        f"{field} should appear in not_triggered_rules when it does not match"
    )


# ---------------------------------------------------------------------------
# CRITICAL_COMBOS — both fields present forces Critical / score >= 90.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("combo_fields,combo_reason", scoring.CRITICAL_COMBOS)
def test_critical_combo_forces_critical_level_and_min_score(combo_fields, combo_reason):
    # Every field used in a combo has trigger_value True in CHECKS.
    normalized = {field: True for field in combo_fields}
    result = scoring.score_token(normalized)

    assert result["risk_level"] == "Critical"
    assert result["score"] >= 90


def test_partial_combo_does_not_force_critical():
    # Only one half of the honeypot+cannot_sell_all combo — must not escalate.
    result = scoring.score_token({"is_honeypot": True})
    assert result["risk_level"] != "Critical"
    assert result["score"] < 90


# ---------------------------------------------------------------------------
# top_holder_percent thresholds: >=50 High/20, >=20 Medium/10, <20 clean.
# ---------------------------------------------------------------------------

def test_top_holder_at_high_cutoff_is_high():
    rule = _find(scoring.score_token({"top_holder_percent": 50})["triggered_rules"], "top_holder_percent")
    assert rule["points"] == 20 and rule["severity"] == "High"


def test_top_holder_just_below_high_is_medium():
    rule = _find(scoring.score_token({"top_holder_percent": 49})["triggered_rules"], "top_holder_percent")
    assert rule["points"] == 10 and rule["severity"] == "Medium"


def test_top_holder_at_medium_cutoff_is_medium():
    rule = _find(scoring.score_token({"top_holder_percent": 20})["triggered_rules"], "top_holder_percent")
    assert rule["points"] == 10 and rule["severity"] == "Medium"


def test_top_holder_just_below_medium_is_clean():
    result = scoring.score_token({"top_holder_percent": 19})
    assert _find(result["triggered_rules"], "top_holder_percent") is None
    assert _find(result["not_triggered_rules"], "top_holder_percent") is not None


# ---------------------------------------------------------------------------
# insider_percent threshold: >=20 High/15, else clean.
# ---------------------------------------------------------------------------

def test_insider_at_cutoff_triggers_high():
    rule = _find(scoring.score_token({"insider_percent": 20})["triggered_rules"], "insider_percent")
    assert rule["points"] == 15 and rule["severity"] == "High"


def test_insider_just_below_cutoff_is_clean():
    result = scoring.score_token({"insider_percent": 19})
    assert _find(result["triggered_rules"], "insider_percent") is None
    assert _find(result["not_triggered_rules"], "insider_percent") is not None


# ---------------------------------------------------------------------------
# top_lp_holder_percent: Critical/25 only when lp_count<=2 AND pct>=60.
# ---------------------------------------------------------------------------

def test_lp_concentrated_triggers_critical():
    rule = _find(
        scoring.score_token({"top_lp_holder_percent": 60, "lp_position_count": 2})["triggered_rules"],
        "top_lp_holder_percent",
    )
    assert rule["points"] == 25 and rule["severity"] == "Critical"


def test_lp_just_below_percent_cutoff_is_clean():
    result = scoring.score_token({"top_lp_holder_percent": 59, "lp_position_count": 2})
    assert _find(result["triggered_rules"], "top_lp_holder_percent") is None
    assert _find(result["not_triggered_rules"], "top_lp_holder_percent") is not None


def test_lp_fragmented_across_many_positions_is_clean():
    # High concentration percent but spread over >2 positions — not a single-party exit risk.
    result = scoring.score_token({"top_lp_holder_percent": 80, "lp_position_count": 3})
    assert _find(result["triggered_rules"], "top_lp_holder_percent") is None
    assert _find(result["not_triggered_rules"], "top_lp_holder_percent") is not None


# ---------------------------------------------------------------------------
# Confidence — known / total, with partial known_signals.
# ---------------------------------------------------------------------------

def test_confidence_partial_known_signals():
    result = scoring.score_token({"_known_signals": 15, "_total_signals": 25})
    assert result["confidence"] == 0.6
    assert result["known_signals"] == 15
    assert result["total_signals"] == 25


def test_confidence_high_partial_rounds_to_two_places():
    result = scoring.score_token({"_known_signals": 23, "_total_signals": 25})
    assert result["confidence"] == 0.92


def test_confidence_defaults_to_zero_when_no_signals():
    result = scoring.score_token({})
    assert result["confidence"] == 0.0
