from __future__ import annotations

import asyncio
import time
from typing import Any

from app.services import chain_adapter, scoring

_CACHE_TTL_SECONDS = 300
_ASSET_CACHE: dict[tuple[str, str, str], tuple[float, dict[str, Any]]] = {}


async def analyze_assets(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks = [_analyze_asset(asset) for asset in assets if (asset.get("address") or asset.get("contract_address"))]
    results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=15.0)
    return [result for result in results if result is not None]


async def _analyze_asset(asset: dict[str, Any]) -> dict[str, Any] | None:
    address = asset.get("address") or asset.get("contract_address")
    if not address:
        return None

    if asset.get("is_native"):
        return {
            "address": address,
            "chain_type": asset.get("chain_type", "solana"),
            "name": asset.get("name") or "Native asset",
            "symbol": asset.get("symbol") or "SOL",
            "risk_score": None,
            "risk_level": "Unscored",
            "analysis_status": "not_applicable",
            "summary": "Native asset — contract analysis is not applicable.",
            "reasons": [],
            "has_audit": False,
            "liquidity_quality": "Not applicable",
            "technical_data": {},
            "is_native": True,
        }

    cache_key = (asset.get("chain_type", "evm"), str(asset.get("chain_id") or ""), address)
    cached = _ASSET_CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]

    try:
        raw, normalized = await asyncio.wait_for(
            chain_adapter.fetch_and_normalize(asset.get("chain_type", "evm"), asset.get("chain_id"), address),
            timeout=15.0,
        )
    except Exception:
        result = {
            "address": address,
            "chain_type": asset.get("chain_type", "evm"),
            "name": asset.get("name") or "Unknown asset",
            "symbol": asset.get("symbol") or "?",
            # An unavailable provider lookup is not a zero-risk result. Keep
            # scoring absent so portfolio/UI code can render it as unscored.
            "risk_score": None,
            "risk_level": "Unscored",
            "analysis_status": "unavailable",
            "summary": "Live analysis could not be completed for this asset.",
            "reasons": [],
            "has_audit": False,
            "liquidity_quality": "Unknown",
            "technical_data": {},
        }
        _ASSET_CACHE[cache_key] = (time.time(), result)
        return result

    score_data = scoring.score_token(normalized)
    reasons = [rule.get("reason") for rule in score_data.get("triggered_rules", []) if rule.get("reason")]
    liquidity_quality = "Excellent" if score_data["score"] <= 30 else "Good" if score_data["score"] <= 60 else "Needs review"
    has_audit = bool(raw.get("audit") or raw.get("audited") or raw.get("audit_status") or raw.get("is_open_source"))
    result = {
        "address": address,
        "chain_type": asset.get("chain_type", "evm"),
        "name": asset.get("name") or normalized.get("token_name") or "Unknown asset",
        "symbol": asset.get("symbol") or normalized.get("token_symbol") or "?",
        "risk_score": score_data["score"],
        "risk_level": score_data["risk_level"],
        "analysis_status": "analyzed",
        "summary": f"{score_data['risk_level']} risk: " + (', '.join(reasons[:2]) if reasons else "No material concerns were triggered."),
        "reasons": reasons,
        "has_audit": has_audit,
        "liquidity_quality": liquidity_quality,
        "technical_data": raw,
    }
    _ASSET_CACHE[cache_key] = (time.time(), result)
    return result
