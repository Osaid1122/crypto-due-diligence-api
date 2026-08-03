from fastapi import APIRouter, Body, HTTPException, Request

from app.models.wallet import WalletAnalyzeRequest, WalletAnalyzeResponse
from app.services.wallet.service import analyze_wallet
from app.core.rate_limit import limiter, ANALYZE_RATE_LIMIT

router = APIRouter(tags=["Wallet analysis"])

WALLET_RESPONSE_EXAMPLE = {
    "status": "success",
    "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "chain_type": "evm",
    "summary": "The portfolio scored 82/100 with a low overall risk profile.",
    "portfolio_score": 82,
    "risk_level": "Low",
    "timeline": [{"ts": "14:32", "step": "Wallet validated"}],
    "assets": [],
    "risk_breakdown": [{"label": "Low risk", "value": 2}],
    "detail_metrics": {"asset_count": 2, "audit_coverage": 50},
    "recommendations": ["Review the highest-risk assets before interacting."],
    "balances": [],
    "transactions": [],
    "metadata": {"provider": "alchemy", "network": "ethereum"},
}


@router.post(
    "/analyze/wallet",
    response_model=WalletAnalyzeResponse,
    response_model_exclude_unset=True,
    summary="Generate a wallet-security assessment",
    description="""
Analyze a wallet using live provider data and return an explainable portfolio
security assessment. The service validates the address, discovers available
assets and activity, analyzes eligible token contracts, and derives an overall
portfolio score.

Omit `chain_type` to infer the network family from the address, or provide it to
explicitly select a supported family. An invalid address or unavailable provider
returns a structured report with `status="error"`; a wallet with no live assets
returns `status="empty"` rather than fabricated data.

Portfolio scores range from 0 to 100, where higher scores represent lower
observed portfolio risk. This report is a due-diligence aid, not investment advice.
""",
    responses={
        200: {"description": "Completed wallet report, including success, empty, and structured error outcomes.", "content": {"application/json": {"example": WALLET_RESPONSE_EXAMPLE}}},
        400: {"description": "The request omitted the wallet address."},
        422: {"description": "The request body was not valid JSON."},
        502: {"description": "An unexpected gateway-level failure occurred while starting the analysis."},
    },
)
@router.post(
    "/wallet/analyze",
    response_model=WalletAnalyzeResponse,
    response_model_exclude_unset=True,
    summary="Generate a wallet-security assessment (compatibility path)",
    description="Compatibility path for `POST /analyze/wallet`. It accepts the same documented request body and returns the same structured wallet-security report.",
    responses={
        200: {"description": "Completed wallet report.", "content": {"application/json": {"example": WALLET_RESPONSE_EXAMPLE}}},
        400: {"description": "The request omitted the wallet address."},
        422: {"description": "The request body was not valid JSON."},
        502: {"description": "An unexpected gateway-level failure occurred while starting the analysis."},
    },
)
@limiter.limit(ANALYZE_RATE_LIMIT)
async def analyze_wallet_route(
    request: Request,
    payload: WalletAnalyzeRequest = Body(
        ...,
        openapi_examples={
            "ethereum_wallet": {
                "summary": "Ethereum wallet",
                "description": "Analyze an EVM wallet using the Ethereum-compatible provider path.",
                "value": {"address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", "chain_type": "evm"},
            },
            "solana_wallet": {
                "summary": "Solana wallet",
                "description": "Analyze a Solana wallet; the chain family can also be inferred from this address.",
                "value": {"address": "FkbQZBcA4Z9XAoZTfSb1gG4FQAa1WUmfBcyG1xzqnsSB", "chain_type": "solana"},
            },
        },
    ),
):
    address = payload.address
    chain_type = payload.chain_type
    if not address:
        raise HTTPException(status_code=400, detail="address is required")

    try:
        return await analyze_wallet(address, chain_type=chain_type)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=502, detail=str(exc)) from exc
