from fastapi import APIRouter, HTTPException

from app.services.wallet.service import analyze_wallet

router = APIRouter(tags=["wallet"])


@router.post("/analyze/wallet")
@router.post("/wallet/analyze")
async def analyze_wallet_route(payload: dict):
    address = (payload or {}).get("address", "")
    chain_type = (payload or {}).get("chain_type")
    if not address:
        raise HTTPException(status_code=400, detail="address is required")

    try:
        return await analyze_wallet(address, chain_type=chain_type)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=502, detail=str(exc)) from exc
