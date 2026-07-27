"""
Chain Adapter — the dispatch layer. Given a chain_type ("evm" or "solana"),
fetches raw provider data via the right adapter and returns it already
normalized into the shared shape scoring.py consumes. This is the one place
in the app that knows two chain types exist; scoring, AI explanation, and
the API response model don't need to.
"""

from app.services import goplus, normalizer, solana_goplus, solana_normalizer
from app.core.config import ANALYSIS_NETWORKS


def get_network(chain_type: str, chain_id: int | None) -> dict:
    """Resolve a request to one explicit network configuration.

    This is deliberately not address-based: Ethereum and X Layer both use
    0x addresses, so only the selected chain ID can safely route an EVM scan.
    """
    if chain_type == "solana":
        return next(network for network in ANALYSIS_NETWORKS if network["key"] == "solana")
    for network in ANALYSIS_NETWORKS:
        if network["family"] == "evm" and network["id"] == chain_id:
            return network
    raise ValueError("Unsupported EVM network. Select a configured GoPlus token-security network and send its chain_id.")


async def fetch_and_normalize(chain_type: str, chain_id: int | None, address: str) -> tuple[dict, dict]:
    """Returns (raw_provider_data, normalized_signals)."""
    network = get_network(chain_type, chain_id)
    if network["family"] == "solana":
        raw = await solana_goplus.get_solana_token_security(address)
        normalized = solana_normalizer.normalize_solana(raw)
        return raw, normalized

    # EVM (default). chain_id presence is enforced by the request model's
    # validator before this is ever called.
    raw = await goplus.get_token_security(str(network["id"]), address)
    normalized = normalizer.normalize(raw)
    return raw, normalized
