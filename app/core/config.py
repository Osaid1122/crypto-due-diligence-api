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

CHAINS_NOT_SUPPORTED_BY_GOPLUS = ["Fantom", "Moonbeam", "Moonriver", "Celo", "Kava"]


class Settings:
    goplus_app_key: str = os.getenv("GOPLUS_APP_KEY", "")
    goplus_app_secret: str = os.getenv("GOPLUS_APP_SECRET", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.5")
    supported_chains: list[dict] = SUPPORTED_CHAINS


@lru_cache
def get_settings() -> Settings:
    return Settings()
