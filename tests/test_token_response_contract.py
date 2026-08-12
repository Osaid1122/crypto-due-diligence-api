"""
Regression tests for the /analyze/token HTTP contract exposing `max_severity`.

The scoring engine has always computed `max_severity` (the single most severe
rule that actually fired — Critical > High > Medium > Low > Informational), and
the AI layer already consumes it. But it was dropped at the HTTP boundary:
TokenAnalyzeResponse never declared the field, so the value the engine computed
never reached the frontend, which then had nothing to trust and re-derived its
own severity. These tests lock the field into the response contract and prove it
carries the engine's OWN value verbatim — never a second, independent calculation.

They drive the REAL app object (no network): upstream fetch is stubbed to return
a fixed normalized dict, REAL scoring runs on it, and the AI layer is stubbed to
a deterministic success so the assertions are about the response shape alone.
"""
import asyncio

import httpx

from app.services import ai, chain_adapter, scoring

VALID_BODY = {
    "address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "chain_type": "evm",
    "chain_id": 1,
}


def _get_app():
    import app.main as m
    return m.app


async def _post(app, json_body) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        return await c.post("/analyze/token", json=json_body)


def _stub_network_and_ai(monkeypatch, normalized):
    """Route the handler to REAL scoring over `normalized`, with a deterministic
    AI success. Only the network and AI edges are faked — scoring is real."""
    def fake_get_network(chain_type, chain_id):
        return {"key": "ethereum", "id": 1}

    async def fake_fetch_and_normalize(chain_type, chain_id, address):
        return ({"token_name": "Test", "token_symbol": "TST"}, normalized)

    async def ai_success(token_name, token_symbol, score_data):
        return {"summary": "ok", "top_concerns": [], "recommended_checks": []}

    monkeypatch.setattr(chain_adapter, "get_network", fake_get_network)
    monkeypatch.setattr(chain_adapter, "fetch_and_normalize", fake_fetch_and_normalize)
    monkeypatch.setattr(ai, "explain_score", ai_success)


def test_max_severity_is_surfaced_and_matches_the_scoring_engine(monkeypatch):
    # A honeypot fires the Critical-severity rule. The response must carry the
    # engine's exact max_severity ("Critical"), not re-derive one from the score.
    normalized = {"is_honeypot": True, "_known_signals": 1, "_total_signals": 10}
    expected = scoring.score_token(normalized)["max_severity"]
    assert expected == "Critical"  # guard: this fixture must exercise a real rule

    _stub_network_and_ai(monkeypatch, normalized)
    resp = asyncio.run(_post(_get_app(), VALID_BODY))

    assert resp.status_code == 200
    body = resp.json()
    assert body["max_severity"] == expected


def test_max_severity_is_distinct_from_risk_level(monkeypatch):
    # The whole point of the field: a lone Critical finding floors risk_level to
    # "High" (not Critical), yet max_severity still reports "Critical". The two
    # are independent, and the response must expose both faithfully.
    normalized = {"is_honeypot": True, "_known_signals": 1, "_total_signals": 10}
    _stub_network_and_ai(monkeypatch, normalized)
    resp = asyncio.run(_post(_get_app(), VALID_BODY))

    body = resp.json()
    assert body["risk_level"] == "High"
    assert body["max_severity"] == "Critical"


def test_max_severity_is_none_when_no_rule_triggers(monkeypatch):
    # A clean token triggers nothing — max_severity is the sentinel "None",
    # surfaced (not omitted) so the frontend never has to guess.
    normalized = {"is_honeypot": False, "_known_signals": 1, "_total_signals": 10}
    _stub_network_and_ai(monkeypatch, normalized)
    resp = asyncio.run(_post(_get_app(), VALID_BODY))

    body = resp.json()
    assert body["max_severity"] == "None"


def test_response_defaults_max_severity_when_scoring_omits_it(monkeypatch):
    # Defensive: an older/partial score_token payload without the key must not
    # break the endpoint — the response falls back to "None" rather than 500ing.
    def fake_get_network(chain_type, chain_id):
        return {"key": "ethereum", "id": 1}

    async def fake_fetch_and_normalize(chain_type, chain_id, address):
        return ({}, {})

    def legacy_score_token(normalized):
        return {
            "score": 18, "risk_level": "Low", "confidence": 0.9,
            "known_signals": 9, "total_signals": 10,
            "reasons": [], "positive_signals": [],
            "triggered_rules": [], "not_triggered_rules": [],
        }  # note: no "max_severity" key

    async def ai_success(token_name, token_symbol, score_data):
        return {"summary": "ok", "top_concerns": [], "recommended_checks": []}

    monkeypatch.setattr(chain_adapter, "get_network", fake_get_network)
    monkeypatch.setattr(chain_adapter, "fetch_and_normalize", fake_fetch_and_normalize)
    monkeypatch.setattr(scoring, "score_token", legacy_score_token)
    monkeypatch.setattr(ai, "explain_score", ai_success)

    resp = asyncio.run(_post(_get_app(), VALID_BODY))
    assert resp.status_code == 200
    assert resp.json()["max_severity"] == "None"
