import os
from functools import lru_cache


# Verified live against GoPlus's own /api/v1/supported_chains?name=token_security
# endpoint on 2026-07-12 — NOT assumed from generic EVM chain ID lists. Some chains
# (Scroll, Mantle, zkSync Era, opBNB, Linea) happen to match their standard EVM chain
# ID here, but that was confirmed, not assumed, since other GoPlus endpoints have
# used non-standard IDs in the past.
#
# Chains intentionally NOT included: Fantom, Moonbeam, Moonriver, Celo, Kava.
# These are genuinely absent from GoPlus's supported_chains response for
# token_security — not a wrong ID, GoPlus does not support them for this endpoint
# at all. Adding fabricated IDs for them would silently fail on every scan.
SUPPORTED_CHAINS: list[dict] = [
    # Ethereum Ecosystem
    {"id": 1, "name": "Ethereum", "ecosystem": "Ethereum Ecosystem"},
    {"id": 42161, "name": "Arbitrum", "ecosystem": "Ethereum Ecosystem"},
    {"id": 10, "name": "Optimism", "ecosystem": "Ethereum Ecosystem"},
    {"id": 8453, "name": "Base", "ecosystem": "Ethereum Ecosystem"},
    {"id": 59144, "name": "Linea", "ecosystem": "Ethereum Ecosystem"},
    {"id": 534352, "name": "Scroll", "ecosystem": "Ethereum Ecosystem"},
    {"id": 324, "name": "zkSync Era", "ecosystem": "Ethereum Ecosystem"},
    # BNB Ecosystem
    {"id": 56, "name": "BNB Chain", "ecosystem": "BNB Ecosystem"},
    {"id": 204, "name": "opBNB", "ecosystem": "BNB Ecosystem"},
    # Other L1s & L2s
    {"id": 137, "name": "Polygon", "ecosystem": "Other L1s & L2s"},
    {"id": 43114, "name": "Avalanche C-Chain", "ecosystem": "Other L1s & L2s"},
    {"id": 25, "name": "Cronos", "ecosystem": "Other L1s & L2s"},
    {"id": 5000, "name": "Mantle", "ecosystem": "Other L1s & L2s"},
    {"id": 100, "name": "Gnosis", "ecosystem": "Other L1s & L2s"},
    # OKX Ecosystem
    {"id": 196, "name": "X Layer", "ecosystem": "OKX Ecosystem"},
]

_NETWORK_KEYS = {
    1: "ethereum", 42161: "arbitrum", 10: "optimism", 8453: "base",
    59144: "linea", 534352: "scroll", 324: "zksync-era", 56: "bnb-chain",
    204: "opbnb", 137: "polygon", 43114: "avalanche-c-chain", 25: "cronos",
    5000: "mantle", 100: "gnosis", 196: "xlayer",
}
_EXPLORERS = {
    1: "https://etherscan.io/address/", 42161: "https://arbiscan.io/address/", 10: "https://optimistic.etherscan.io/address/",
    8453: "https://basescan.org/address/", 59144: "https://lineascan.build/address/", 534352: "https://scrollscan.com/address/",
    324: "https://explorer.zksync.io/address/", 56: "https://bscscan.com/address/", 204: "https://mainnet.opbnbscan.com/address/",
    137: "https://polygonscan.com/address/", 43114: "https://snowtrace.io/address/", 25: "https://explorer.cronos.org/address/",
    5000: "https://mantlescan.xyz/address/", 100: "https://gnosisscan.io/address/", 196: "https://www.okx.com/web3/explorer/xlayer/address/",
}

# Product networks are exactly the GoPlus token-security networks verified
# above, plus Solana. "evm" remains a family; the caller must supply one of
# these explicit chain IDs because a 0x address cannot identify its chain.
ANALYSIS_NETWORKS: list[dict] = [
    {"key": _NETWORK_KEYS[chain["id"]], "id": chain["id"], "name": chain["name"], "family": "evm", "address_type": "evm", "explorer": _EXPLORERS[chain["id"]], "token_security": True, "wallet_analysis": chain["id"] == 1}
    for chain in SUPPORTED_CHAINS
] + [
    {"key": "solana", "id": None, "name": "Solana", "family": "solana", "address_type": "solana", "explorer": "https://solscan.io/token/", "token_security": True, "wallet_analysis": True},
]

CHAINS_NOT_SUPPORTED_BY_GOPLUS = ["Fantom", "Moonbeam", "Moonriver", "Celo", "Kava"]


class Settings:
    goplus_app_key: str = os.getenv("GOPLUS_APP_KEY", "")
    goplus_app_secret: str = os.getenv("GOPLUS_APP_SECRET", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.5")
    supported_chains: list[dict] = SUPPORTED_CHAINS
    analysis_networks: list[dict] = ANALYSIS_NETWORKS


@lru_cache
def get_settings() -> Settings:
    return Settings()
