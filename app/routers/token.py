import os
from typing import Any

from fastapi import APIRouter, Body, Header, HTTPException, Query, Request

from app.models.token import TokenAnalyzeRequest, TokenAnalyzeResponse
from app.services import chain_adapter, goplus, scoring, ai
from app.core.rate_limit import limiter, ANALYZE_RATE_LIMIT

router = APIRouter(prefix="/analyze", tags=["Token analysis"])

TOKEN_RESPONSE_EXAMPLE: dict[str, Any] = {
    "token_name": "USD Coin",
    "token_symbol": "USDC",
    "chain_type": "evm",
    "network": "ethereum",
    "chain_id": 1,
    "risk_score": 18,
    "risk_level": "Low",
    "confidence": 0.92,
    "confidence_known_signals": 23,
    "confidence_total_signals": 25,
    "summary": "The deterministic assessment found a low-risk profile based on available provider signals.",
    "top_concerns": ["Review current ownership and liquidity conditions before interacting."],
    "recommended_checks": ["Verify the contract address through an official project source."],
    "positive_signals": ["No unrestricted mint function was reported."],
    "triggered_rules": [],
    "not_triggered_rules": [{"field": "mintable", "reason": "No unrestricted minting signal reported."}],
    "normalized_signals": {"is_mintable": False, "is_honeypot": False},
    "technical_data": {"token_name": "USD Coin"},
}

RAW_PROVIDER_RESPONSE_EXAMPLE: dict[str, Any] = {
    "result": {
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {
            "token_name": "USD Coin",
            "token_symbol": "USDC",
            "is_honeypot": "0",
        }
    }
}


@router.post(
    "/token",
    response_model=TokenAnalyzeResponse,
    summary="Generate a token-security assessment",
    description="""
Generate a provider-backed, deterministic security assessment for an ERC-20 token
or Solana SPL mint. The API normalizes live security data, applies transparent
risk rules, and returns both the underlying signals and an AI-assisted explanation.

Use `chain_type="evm"` with a supported `chain_id` for EVM contracts. Use
`chain_type="solana"` for SPL mints; `chain_id` is not needed for Solana.

The `risk_score` expresses detected risk from 0 (lowest) to 100 (highest). It is
not investment advice; always independently verify an address and current on-chain state.
""",
    responses={
        200: {"description": "Completed token-security report.", "content": {"application/json": {"example": TOKEN_RESPONSE_EXAMPLE}}},
        404: {"description": "The requested network is not configured or was not found."},
        422: {"description": "The request did not contain a valid address or chain selection."},
        502: {"description": "The upstream token-security provider could not complete the lookup."},
    },
)
@limiter.limit(ANALYZE_RATE_LIMIT)
async def analyze_token(
    request: Request,
    payload: TokenAnalyzeRequest = Body(
        ...,
        openapi_examples={
            "ethereum_usdc": {
                "summary": "Ethereum ERC-20 token",
                "description": "Analyze the USDC contract on Ethereum mainnet.",
                "value": {"address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "chain_type": "evm", "chain_id": 1},
            },
            "solana_wrapped_sol": {
                "summary": "Solana SPL mint",
                "description": "Analyze wrapped SOL through the Solana security-data path.",
                "value": {"address": "So11111111111111111111111111111111111111112", "chain_type": "solana"},
            },
        },
    ),
):
    try:
        network = chain_adapter.get_network(payload.chain_type, payload.chain_id)
        raw, normalized = await chain_adapter.fetch_and_normalize(
            payload.chain_type, payload.chain_id, payload.address
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GoPlus lookup failed: {e}")

    # Defense in depth: everything below runs AFTER the GoPlus try/except, so an
    # unexpected exception here (scoring bug, or an AI failure that somehow
    # escapes explain_score's own fallback) would otherwise propagate to
    # Starlette's ServerErrorMiddleware as a raw 500 — which is generated
    # OUTSIDE CORSMiddleware and therefore has no Access-Control-Allow-Origin,
    # surfacing in the browser as a CORS error. Converting it to an
    # HTTPException keeps the response inside CORSMiddleware so it retains CORS
    # headers. This is a backstop; explain_score (Fix A) already degrades
    # gracefully, so this path should effectively never be hit.
    try:
        score_data = scoring.score_token(normalized)

        token_name = normalized.get("token_name")
        token_symbol = normalized.get("token_symbol")

        explanation = await ai.explain_score(token_name or "Unknown token", token_symbol or "?", score_data)
    except HTTPException:
        raise  # already a structured API error; let it through unchanged
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI explanation failed: {e}")

    normalized_display = {
        k: v for k, v in normalized.items() if not k.startswith("_")
    }

    return TokenAnalyzeResponse(
        token_name=token_name,
        token_symbol=token_symbol,
        chain_type=payload.chain_type,
        network=network["key"],
        chain_id=network["id"],
        risk_score=score_data["score"],
        risk_level=score_data["risk_level"],
        confidence=score_data["confidence"],
        confidence_known_signals=score_data["known_signals"],
        confidence_total_signals=score_data["total_signals"],
        summary=explanation["summary"],
        top_concerns=explanation["top_concerns"],
        recommended_checks=explanation["recommended_checks"],
        positive_signals=score_data.get("positive_signals", []),
        triggered_rules=score_data["triggered_rules"],
        not_triggered_rules=score_data["not_triggered_rules"],
        normalized_signals=normalized_display,
        technical_data=raw,
    )


@router.get(
    "/token/raw",
    summary="Retrieve raw EVM token-security provider data",
    description="""
Return the unprocessed EVM token-security payload from the upstream provider.

This diagnostic endpoint does not normalize data, calculate a risk score, or
generate an explanation. Use `POST /analyze/token` for the public security report.
`chain_id` must identify a provider-supported EVM network, and `address` must be
an EVM contract address.
""",
    responses={
        200: {"description": "Raw upstream provider payload. Fields vary by network and provider response.", "content": {"application/json": {"example": RAW_PROVIDER_RESPONSE_EXAMPLE}}},
        404: {"description": "The requested chain is not supported by the upstream provider."},
        422: {"description": "A required query parameter was missing or invalid."},
        502: {"description": "The upstream token-security provider could not complete the lookup."},
    },
)
async def analyze_token_raw(
    chain_id: int = Query(..., description="Provider-supported EVM chain ID, such as 1 for Ethereum or 196 for X Layer.", examples=[1]),
    address: str = Query(..., description="0x-prefixed EVM token contract address to inspect.", examples=["0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"]),
    x_debug_key: str | None = Header(default=None, alias="X-Debug-Key"),
):
    # Debug-only endpoint. It's gated behind a shared secret and returns 404 —
    # not 401/403 — for a missing/wrong key (and when DEBUG_API_KEY is unset), so
    # its existence isn't revealed to unauthorized callers.
    debug_key = os.getenv("DEBUG_API_KEY")
    if not debug_key or x_debug_key != debug_key:
        raise HTTPException(status_code=404, detail="Not Found")

    try:
        raw = await goplus.get_token_security(str(chain_id), address)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GoPlus lookup failed: {e}")
    return raw
