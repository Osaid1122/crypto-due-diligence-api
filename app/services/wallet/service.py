from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from app.services.wallet.analyzer import analyze_assets
from app.services.wallet.providers import detect_chain_type, fetch_wallet_portfolio, validate_wallet_address
from app.services.wallet.scoring import build_portfolio_score
from app.services.wallet.summary import build_summary


async def analyze_wallet(address: str, chain_type: Optional[str] = None, provider: Optional[Callable[..., Any]] = None) -> dict[str, Any]:
    now = lambda: datetime.now(timezone.utc).strftime("%H:%M")
    timeline: list[dict[str, Any]] = [{"ts": now(), "step": "Wallet connected"}]
    detected_chain = detect_chain_type(address, chain_type)

    if not validate_wallet_address(address, detected_chain):
        return {
            "status": "error",
            "address": address,
            "chain_type": detected_chain,
            "chain": detected_chain,
            "summary": "The provided wallet address is invalid for the detected chain.",
            "message": "The provided wallet address is invalid for the selected chain.",
            "portfolio_score": 0,
            "risk_level": "Unknown",
            "timeline": timeline + [{"ts": now(), "step": "Validation failed"}],
            "assets": [],
            "risk_breakdown": [],
            "detail_metrics": {},
            "recommendations": [],
            "error_code": "INVALID_ADDRESS",
        }

    timeline.append({"ts": now(), "step": "Wallet validated"})

    provider_fn = provider or _default_provider
    try:
        payload = await asyncio.wait_for(provider_fn(detected_chain, address), timeout=15.0)
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "address": address,
            "chain_type": detected_chain,
            "chain": detected_chain,
            "summary": "Wallet analysis timed out while fetching live provider data.",
            "message": "Wallet data could not be retrieved from the selected provider.",
            "portfolio_score": 0,
            "risk_level": "Unknown",
            "timeline": timeline + [{"ts": now(), "step": "Data fetch timed out"}],
            "assets": [],
            "risk_breakdown": [],
            "detail_metrics": {"error_code": "provider_timeout"},
            "recommendations": [],
            "error_code": "PROVIDER_UNAVAILABLE",
        }
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "status": "error",
            "address": address,
            "chain_type": detected_chain,
            "chain": detected_chain,
            "summary": "Wallet data could not be retrieved from the selected provider.",
            "message": "Wallet data could not be retrieved from the selected provider.",
            "portfolio_score": 0,
            "risk_level": "Unknown",
            "timeline": timeline + [{"ts": now(), "step": "Data fetch failed"}],
            "assets": [],
            "risk_breakdown": [],
            "detail_metrics": {"error_code": "PROVIDER_UNAVAILABLE", "provider_message": str(exc), "chain": detected_chain},
            "recommendations": [],
            "error_code": "PROVIDER_UNAVAILABLE",
        }

    assets = payload.get("assets") or []
    balances = payload.get("balances") or []
    transactions = payload.get("transactions") or []
    metadata = payload.get("metadata") or {}
    has_live_data = bool(assets or balances or transactions or payload.get("nft_count") or metadata)

    if not has_live_data:
        return {
            "status": "empty",
            "address": address,
            "chain_type": detected_chain,
            "summary": "No live wallet assets were found for this address. The analysis is intentionally empty rather than using mock data.",
            "portfolio_score": 0,
            "risk_level": "Unknown",
            "timeline": timeline + [
                {"ts": now(), "step": "Assets retrieved"},
                {"ts": now(), "step": "Analysis completed"},
            ],
            "assets": [],
            "risk_breakdown": [],
            "detail_metrics": {
                "asset_count": 0,
                "nft_count": payload.get("nft_count", 0),
                "transaction_count": len(transactions),
                "wallet_metadata": metadata,
            },
            "recommendations": [],
            "error_code": "PROVIDER_NO_DATA",
        }

    timeline.append({"ts": now(), "step": "Assets retrieved"})
    try:
        analyzed_assets = await asyncio.wait_for(analyze_assets(assets), timeout=15.0)
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "address": address,
            "chain_type": detected_chain,
            "summary": "Wallet analysis timed out while evaluating the portfolio assets.",
            "portfolio_score": 0,
            "risk_level": "Unknown",
            "timeline": timeline + [{"ts": now(), "step": "Asset analysis timed out"}],
            "assets": [],
            "risk_breakdown": [],
            "detail_metrics": {"error_code": "asset_analysis_timeout"},
            "recommendations": [],
            "error_code": "asset_analysis_timeout",
        }
    score = build_portfolio_score(analyzed_assets)
    score["detail_metrics"] = {
        **score.get("detail_metrics", {}),
        "asset_count": len(analyzed_assets),
        "nft_count": payload.get("nft_count", 0),
        "transaction_count": len(transactions),
        "wallet_metadata": metadata,
        "balance_count": len(balances),
    }
    summary = build_summary(
        analyzed_assets,
        score,
        wallet_context={
            "nft_count": payload.get("nft_count", 0),
            "transaction_count": len(transactions),
            "provider": metadata.get("provider"),
        },
    )

    return {
        "status": "success",
        "address": address,
        "chain_type": detected_chain,
        "summary": summary,
        "portfolio_score": score["score"],
        "risk_level": score["risk_level"],
        "timeline": timeline + [
            {"ts": now(), "step": f"{len(analyzed_assets)} assets analyzed"},
            {"ts": now(), "step": "Portfolio score generated"},
            {"ts": now(), "step": "Analysis completed"},
        ],
        "assets": analyzed_assets,
        "risk_breakdown": score["risk_breakdown"],
        "detail_metrics": score.get("detail_metrics", {}),
        "recommendations": score["recommendations"],
        "balances": balances,
        "transactions": transactions,
        "metadata": metadata,
    }


async def _default_provider(chain_type: str, address: str) -> dict[str, Any]:
    return await fetch_wallet_portfolio(chain_type, address)
