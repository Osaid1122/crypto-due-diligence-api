from __future__ import annotations

from typing import Any

from app.services.wallet.scoring import is_numeric_risk_score


def build_summary(assets: list[dict[str, Any]], score: dict[str, Any], wallet_context: dict[str, Any] | None = None) -> str:
    wallet_context = wallet_context or {}
    nft_count = wallet_context.get("nft_count", 0)
    transaction_count = wallet_context.get("transaction_count", 0)
    provider = wallet_context.get("provider")

    if not assets:
        if nft_count or transaction_count:
            return (
                f"Live wallet data surfaced {nft_count} NFT(s) and {transaction_count} transaction(s), "
                f"but no fungible token balances were returned by the active provider."
            )
        return "No live wallet assets were found for this address. The analysis remains empty rather than fabricating portfolio data."

    provider_suffix = f" via {provider}" if provider else ""
    scored_assets = [asset for asset in assets if is_numeric_risk_score(asset.get("risk_score"))]
    if not scored_assets:
        return (
            f"Live assets were returned{provider_suffix}, but no eligible asset received a contract-security score. "
            "Unavailable or native assets remain unscored rather than being treated as safe."
        )

    highest = max(scored_assets, key=lambda item: item["risk_score"])
    return (
        f"The portfolio scored {score['score']}/100 with a {score['risk_level'].lower()} overall risk profile"
        f"{provider_suffix}. The most concerning asset is {highest.get('name', 'an asset')} at {highest.get('risk_score', 0)}/100."
        f" The wallet also reported {nft_count} NFT(s) and {transaction_count} transaction(s)."
    )
