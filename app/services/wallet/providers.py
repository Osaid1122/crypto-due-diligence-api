from __future__ import annotations

import asyncio
import os
import re
from typing import Any, Optional, Protocol

import httpx
import logging

EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
SOLANA_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


class WalletProvider(Protocol):
    async def fetch_wallet_data(self, chain_type: str, address: str) -> dict[str, Any]:
        ...


class AlchemyProvider:
    async def fetch_wallet_data(self, chain_type: str, address: str) -> dict[str, Any]:
        api_key = os.getenv("ALCHEMY_API_KEY") or os.getenv("ALCHEMY_API_KEY_ETH")
        if not api_key:
            raise RuntimeError("Alchemy API key not configured")

        base_url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_res = await asyncio.wait_for(client.get(f"{base_url}/getTokenBalances", params={"address": address}), timeout=15.0)
            token_res.raise_for_status()
            token_payload = token_res.json()

            assets: list[dict[str, Any]] = []
            for item in token_payload.get("tokenBalances", []) or []:
                contract = item.get("contractAddress")
                balance = item.get("tokenBalance") or "0"
                if not contract:
                    continue
                assets.append({
                    "address": contract,
                    "chain_type": "evm",
                    "chain_id": 1,
                    "name": item.get("name") or "Unknown token",
                    "symbol": item.get("symbol") or "?",
                    "balance": balance,
                    "decimals": item.get("decimals") or 18,
                })

            nft_res = await asyncio.wait_for(client.get(f"{base_url}/getNFTs", params={"owner": address, "pageSize": 100}), timeout=15.0)
            nft_res.raise_for_status()
            nft_payload = nft_res.json()
            nft_count = int(nft_payload.get("totalCount") or 0)

            transfer_res = await asyncio.wait_for(client.get(
                f"{base_url}/getAssetTransfers",
                params={
                    "fromAddress": address,
                    "toAddress": address,
                    "category": ["external", "erc20", "erc721", "erc1155"],
                    "maxCount": 100,
                },
            ), timeout=15.0)
            transfer_res.raise_for_status()
            transfer_payload = transfer_res.json()
            transactions = transfer_payload.get("transfers") or []

            return {
                "assets": assets,
                "balances": assets,
                "transactions": transactions,
                "nft_count": nft_count,
                "metadata": {"provider": "alchemy", "network": "ethereum"},
            }


class MoralisProvider:
    async def fetch_wallet_data(self, chain_type: str, address: str) -> dict[str, Any]:
        """Fetch wallet data using Moralis Data API (v2.2).

        Uses the unified Wallet endpoints documented at https://docs.moralis.com/data-api
        Falls back to defensive parsing so the rest of the pipeline keeps its expected schema.
        """
        api_key = os.getenv("MORALIS_API_KEY")
        if not api_key:
            raise RuntimeError("Moralis API key not configured")

        logger = logging.getLogger(__name__)
        base_url = os.getenv("MORALIS_BASE_URL", "https://deep-index.moralis.io/api/v2.2")
        headers = {"x-api-key": api_key}

        # Determine chain param for Moralis (use 'eth' for evm)
        chain_param = "eth" if chain_type != "solana" else "solana"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Token balances: /wallets/{address}/tokens
                token_resp = await asyncio.wait_for(
                    client.get(f"{base_url}/wallets/{address}/tokens", params={"chain": chain_param}, headers=headers),
                    timeout=15.0,
                )
                token_resp.raise_for_status()
                token_payload = token_resp.json()
            except httpx.HTTPStatusError as exc:
                logger.warning("Moralis token balances request failed: %s %s", exc.response.status_code, exc.response.text)
                token_payload = {}
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Moralis token balances request error: %s", exc)
                token_payload = {}

            assets: list[dict[str, Any]] = []
            # Moralis may return tokens under different keys depending on endpoint/version
            tokens_list = []
            if isinstance(token_payload, dict):
                # new Data API often returns `result` or `tokens`
                tokens_list = token_payload.get("result") or token_payload.get("tokens") or token_payload.get("tokenBalances") or []
            elif isinstance(token_payload, list):
                tokens_list = token_payload

            for item in tokens_list or []:
                # Normalise fields across possible Moralis responses
                contract = item.get("contract_address") or item.get("token_address") or item.get("address") or item.get("tokenAddress")
                if not contract:
                    continue
                balance = item.get("balance") or item.get("amount") or item.get("tokenBalance") or item.get("raw_balance") or "0"
                decimals = item.get("decimals") or item.get("token_decimals") or item.get("tokenDecimal") or 18
                assets.append({
                    "address": contract,
                    "chain_type": "evm",
                    "chain_id": 1,
                    "name": item.get("name") or item.get("token_name") or "Unknown token",
                    "symbol": item.get("symbol") or item.get("token_symbol") or "?",
                    "balance": balance,
                    "decimals": decimals,
                })

            # NFTs: /{address}/nft (per docs)
            try:
                nft_resp = await asyncio.wait_for(
                    client.get(f"{base_url}/{address}/nft", params={"chain": chain_param, "format": "decimal"}, headers=headers),
                    timeout=15.0,
                )
                nft_resp.raise_for_status()
                nft_payload = nft_resp.json()
            except httpx.HTTPStatusError as exc:
                logger.warning("Moralis NFT request failed: %s %s", exc.response.status_code, exc.response.text)
                nft_payload = {}
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Moralis NFT request error: %s", exc)
                nft_payload = {}

            nft_count = 0
            if isinstance(nft_payload, dict):
                nft_count = len(nft_payload.get("result", []))
            elif isinstance(nft_payload, list):
                nft_count = len(nft_payload)

            # Transactions: wallet native txs endpoint is /{address}
            try:
                tx_resp = await asyncio.wait_for(
                    client.get(f"{base_url}/{address}", params={"chain": chain_param}, headers=headers),
                    timeout=20.0,
                )
                tx_resp.raise_for_status()
                tx_payload = tx_resp.json()
            except httpx.HTTPStatusError as exc:
                logger.warning("Moralis transactions request failed: %s %s", exc.response.status_code, exc.response.text)
                tx_payload = []
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Moralis transactions request error: %s", exc)
                tx_payload = []

            # Normalise transactions to a list
            transactions: list[Any] = []
            if isinstance(tx_payload, dict):
                transactions = tx_payload.get("result") or tx_payload.get("transfers") or tx_payload.get("transactions") or []
            elif isinstance(tx_payload, list):
                transactions = tx_payload

            return {
                "assets": assets,
                "balances": assets,
                "transactions": transactions,
                "nft_count": nft_count,
                "metadata": {"provider": "moralis", "network": "ethereum"},
            }


class HeliusProvider:
    async def fetch_wallet_data(self, chain_type: str, address: str) -> dict[str, Any]:
        api_key = os.getenv("HELIUS_API_KEY")
        if not api_key:
            raise RuntimeError("Helius API key not configured")

        logger = logging.getLogger(__name__)
        rpc_url = os.getenv("HELIUS_RPC_URL", "https://mainnet.helius-rpc.com/")
        transaction_url = os.getenv("HELIUS_TRANSACTION_URL", "https://api-mainnet.helius-rpc.com/v0")
        auth_params = {"api-key": api_key}

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Helius DAS is the supported wallet-assets API. The old
            # /v1/wallet/{address}/balances route returns 404 and must not be
            # treated as an empty portfolio.
            try:
                assets_resp = await asyncio.wait_for(
                    client.post(
                        rpc_url,
                        params=auth_params,
                        headers={"Content-Type": "application/json"},
                        json={
                            "jsonrpc": "2.0",
                            "id": "wallet-scanner",
                            "method": "getAssetsByOwner",
                            "params": {
                                "ownerAddress": address,
                                "page": 1,
                                "limit": 100,
                                "displayOptions": {"showFungible": True, "showNativeBalance": True},
                            },
                        },
                    ),
                    timeout=15.0,
                )
                assets_resp.raise_for_status()
                assets_payload = assets_resp.json()
                if assets_payload.get("error"):
                    raise RuntimeError(f"Helius DAS error: {assets_payload['error']}")
            except httpx.HTTPStatusError as exc:
                logger.warning("Helius DAS assets request failed: status=%s body=%s", exc.response.status_code, exc.response.text)
                raise RuntimeError(f"Helius asset retrieval failed with HTTP {exc.response.status_code}") from exc

            assets: list[dict[str, Any]] = []
            result = assets_payload.get("result") or {}
            native_balance = result.get("nativeBalance") or result.get("native_balance")
            if isinstance(native_balance, dict) and native_balance.get("lamports") is not None:
                assets.append({
                    "address": "native-sol",
                    "chain_type": "solana",
                    "name": "Solana",
                    "symbol": "SOL",
                    "balance": str(native_balance.get("lamports")),
                    "decimals": 9,
                    "is_native": True,
                })
            for item in (result.get("items") or []):
                mint = item.get("id") or item.get("mint")
                if not mint:
                    continue
                metadata = (item.get("content") or {}).get("metadata") or {}
                token_info = item.get("token_info") or item.get("tokenInfo") or {}
                if not token_info and item.get("interface") not in {"FungibleToken", "FungibleAsset"}:
                    continue
                assets.append({
                    "address": mint,
                    "chain_type": "solana",
                    "name": metadata.get("name") or item.get("name") or mint,
                    "symbol": metadata.get("symbol") or item.get("symbol") or "?",
                    "balance": str(token_info.get("balance") or item.get("balance") or "0"),
                    "decimals": token_info.get("decimals") or item.get("decimals") or 0,
                })

            # Enhanced Transactions is the supported address-history endpoint.
            try:
                tx_resp = await asyncio.wait_for(
                    client.get(f"{transaction_url}/addresses/{address}/transactions", params={**auth_params, "limit": 100},
                    timeout=20.0,
                )
                tx_resp.raise_for_status()
                tx_payload = tx_resp.json()
            except httpx.HTTPStatusError as exc:
                logger.warning("Helius transaction request failed: status=%s body=%s", exc.response.status_code, exc.response.text)
                raise RuntimeError(f"Helius transaction retrieval failed with HTTP {exc.response.status_code}") from exc

            transactions = tx_payload if isinstance(tx_payload, list) else []

            nft_count = sum(1 for item in (result.get("items") or []) if item.get("interface") not in {"FungibleToken", "FungibleAsset"})

            return {
                "assets": assets,
                "balances": assets,
                "transactions": transactions or [],
                "nft_count": nft_count,
                "metadata": {"provider": "helius", "network": "solana", "asset_endpoint": "getAssetsByOwner", "transaction_endpoint": "enhanced_transactions"},
            }


class BirdeyeProvider:
    async def fetch_wallet_data(self, chain_type: str, address: str) -> dict[str, Any]:
        raise RuntimeError("Birdeye provider not configured")


async def fetch_wallet_portfolio(chain_type: str, address: str, provider: Optional[WalletProvider] = None) -> dict[str, Any]:
    if provider is not None:
        return await provider.fetch_wallet_data(chain_type, address)

    providers: list[WalletProvider] = [MoralisProvider(), AlchemyProvider()] if chain_type != "solana" else [HeliusProvider(), BirdeyeProvider()]
    last_error: Optional[Exception] = None
    for provider_instance in providers:
        try:
            return await asyncio.wait_for(provider_instance.fetch_wallet_data(chain_type, address), timeout=15.0)
        except asyncio.TimeoutError as exc:  # pragma: no cover - defensive fallback
            last_error = TimeoutError("Wallet provider request timed out")
        except Exception as exc:  # pragma: no cover - defensive fallback
            last_error = exc
    if last_error is not None:
        raise RuntimeError(f"No wallet provider could fetch data: {last_error}") from last_error
    return {"assets": [], "balances": [], "transactions": [], "nft_count": 0, "metadata": {}}


def detect_chain_type(address: str, chain_type: Optional[str] = None) -> str:
    if chain_type:
        return chain_type
    if EVM_ADDRESS_RE.match(address):
        return "evm"
    if SOLANA_ADDRESS_RE.match(address):
        return "solana"
    return "evm"


def validate_wallet_address(address: str, chain_type: str) -> bool:
    normalized = (address or '').strip()
    if not normalized:
        return False
    if chain_type == "solana":
        return bool(SOLANA_ADDRESS_RE.match(normalized))
    return bool(EVM_ADDRESS_RE.match(normalized))
