"""
Chain Adapter — the dispatch layer. Given a chain_type ("evm" or "solana"),
fetches raw provider data via the right adapter and returns it already
normalized into the shared shape scoring.py consumes. This is the one place
in the app that knows two chain types exist; scoring, AI explanation, and
the API response model don't need to.
"""

from app.services import goplus, normalizer, solana_goplus, solana_normalizer


async def fetch_and_normalize(chain_type: str, chain_id: int | None, address: str) -> tuple[dict, dict]:
    """Returns (raw_provider_data, normalized_signals)."""
    if chain_type == "solana":
        raw = await solana_goplus.get_solana_token_security(address)
        normalized = solana_normalizer.normalize_solana(raw)
        return raw, normalized

    # EVM (default). chain_id presence is enforced by the request model's
    # validator before this is ever called.
    raw = await goplus.get_token_security(str(chain_id), address)
    normalized = normalizer.normalize(raw)
    return raw, normalized
