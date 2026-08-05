"""
Regression tests for the intermittent production CORS failure.

Root cause: when the AI layer raised (OpenAI 429 / timeout / connection error),
the exception escaped the /analyze/token handler and became a Starlette 500
generated OUTSIDE CORSMiddleware, so the response had no
Access-Control-Allow-Origin. Chrome reported that as a CORS error.

These tests drive the REAL app object (no network) and assert:
  1. OPTIONS preflight returns 200 + Access-Control-Allow-Origin.
  2. A successful POST returns 200 + Access-Control-Allow-Origin.
  3. When the AI upstream fails, the endpoint does NOT return a raw 500 and the
     response STILL carries Access-Control-Allow-Origin — either as a 200 with
     the templated fallback (preferred, Fix A) or a structured 502 (Fix B).
"""
import asyncio

import httpx
import pytest

from app.services import ai, chain_adapter, scoring

ORIGIN = "https://cryptoduediligence.dev"
VALID_BODY = {
    "address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "chain_type": "evm",
    "chain_id": 1,
}


def _get_app():
    # Imported lazily so ALLOWED_ORIGINS is read at import time inside the test env.
    import app.main as m
    return m.app


def _acao(resp: httpx.Response) -> str | None:
    return resp.headers.get("access-control-allow-origin")


async def _call(app, method: str, headers: dict, json_body=None) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        if method == "OPTIONS":
            return await c.options("/analyze/token", headers=headers)
        return await c.post("/analyze/token", headers=headers, json=json_body)


def _stub_upstream(monkeypatch):
    """Make the handler reach ai.explain_score deterministically, no network."""
    def fake_get_network(chain_type, chain_id):
        return {"key": "ethereum", "id": 1}

    async def fake_fetch_and_normalize(chain_type, chain_id, address):
        return ({"raw": "provider-data"}, {"token_name": "USD Coin", "token_symbol": "USDC"})

    def fake_score_token(normalized):
        return {
            "score": 18, "risk_level": "Low", "confidence": 0.92,
            "known_signals": 23, "total_signals": 25,
            "reasons": [], "positive_signals": [],
            "triggered_rules": [], "not_triggered_rules": [],
        }

    monkeypatch.setattr(chain_adapter, "get_network", fake_get_network)
    monkeypatch.setattr(chain_adapter, "fetch_and_normalize", fake_fetch_and_normalize)
    monkeypatch.setattr(scoring, "score_token", fake_score_token)


def test_preflight_options_returns_cors_headers(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", ORIGIN)
    resp = asyncio.run(_call(_get_app(), "OPTIONS", {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }))
    assert resp.status_code == 200
    assert _acao(resp) == ORIGIN


def test_successful_post_returns_200_with_cors(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", ORIGIN)
    _stub_upstream(monkeypatch)

    async def ai_success(token_name, token_symbol, score_data):
        return {"summary": "ok", "top_concerns": [], "recommended_checks": []}

    monkeypatch.setattr(ai, "explain_score", ai_success)

    resp = asyncio.run(_call(_get_app(), "POST", {"Origin": ORIGIN}, VALID_BODY))
    assert resp.status_code == 200
    assert _acao(resp) == ORIGIN


@pytest.mark.parametrize("exc", [
    httpx.HTTPStatusError(
        "429 Too Many Requests",
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        response=httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com")),
    ),
    httpx.TimeoutException("request timed out"),
    httpx.ConnectError("connection refused"),
])
def test_ai_failure_never_produces_raw_500_without_cors(monkeypatch, exc):
    """The core regression: an AI upstream failure must not surface as a
    CORS-less 500. We patch the REAL explain_score to raise, so this exercises
    Fix B (router guard). Fix A is covered separately below."""
    monkeypatch.setenv("ALLOWED_ORIGINS", ORIGIN)
    _stub_upstream(monkeypatch)

    async def ai_boom(token_name, token_symbol, score_data):
        raise exc

    monkeypatch.setattr(ai, "explain_score", ai_boom)

    resp = asyncio.run(_call(_get_app(), "POST", {"Origin": ORIGIN}, VALID_BODY))

    # Must NOT be a raw 500...
    assert resp.status_code != 500, f"raw 500 escaped for {type(exc).__name__}"
    # ...and the browser must still see CORS headers.
    assert _acao(resp) == ORIGIN, f"missing ACAO for {type(exc).__name__}"
    # Structured error, not a bare text/plain 500.
    assert resp.status_code == 502


def test_ai_layer_degrades_to_fallback_on_upstream_error(monkeypatch):
    """Fix A end-to-end: with a real (fake) OpenAI key set, a 429 from the
    upstream must degrade to the templated fallback and yield a 200 report with
    CORS headers — the preferred outcome (no error surfaced to the browser)."""
    monkeypatch.setenv("ALLOWED_ORIGINS", ORIGIN)
    _stub_upstream(monkeypatch)

    # Force explain_score down its real network path with a key present...
    from app.core import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-key", raising=False)

    # Fail ONLY the OpenAI call; delegate every other POST (including the ASGI
    # test client's own POST to the app) to the real implementation.
    real_post = httpx.AsyncClient.post

    async def fake_post(self, url, **kwargs):
        if "openai.com" in str(url):
            req = httpx.Request("POST", url)
            return httpx.Response(429, request=req, text="Too Many Requests")
        return await real_post(self, url, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    resp = asyncio.run(_call(_get_app(), "POST", {"Origin": ORIGIN}, VALID_BODY))
    assert resp.status_code == 200, "AI outage should degrade to fallback, not error"
    assert _acao(resp) == ORIGIN
    body = resp.json()
    # Fallback summary shape from ai.explain_score
    assert "scored 18/100" in body["summary"]
