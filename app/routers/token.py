from fastapi import APIRouter, HTTPException

from app.models.token import TokenAnalyzeRequest, TokenAnalyzeResponse
from app.services import chain_adapter, goplus, scoring, ai

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("/token", response_model=TokenAnalyzeResponse)
async def analyze_token(payload: TokenAnalyzeRequest):
    try:
        raw, normalized = await chain_adapter.fetch_and_normalize(
            payload.chain_type, payload.chain_id, payload.address
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GoPlus lookup failed: {e}")

    score_data = scoring.score_token(normalized)

    token_name = normalized.get("token_name")
    token_symbol = normalized.get("token_symbol")

    explanation = await ai.explain_score(token_name or "Unknown token", token_symbol or "?", score_data)

    normalized_display = {
        k: v for k, v in normalized.items() if not k.startswith("_")
    }

    return TokenAnalyzeResponse(
        token_name=token_name,
        token_symbol=token_symbol,
        chain_type=payload.chain_type,
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


@router.get("/token/raw")
async def analyze_token_raw(chain_id: int, address: str):
    """Debug endpoint: returns the raw GoPlus EVM response with no scoring or
    AI layer. Useful for inspecting real fields before tuning the scoring
    engine. EVM-only — kept as-is; Solana debugging goes through
    scripts/validate_solana.py during development instead."""
    try:
        raw = await goplus.get_token_security(str(chain_id), address)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GoPlus lookup failed: {e}")
    return raw
