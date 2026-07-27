import asyncio

from app.services import chain_adapter


def test_evm_provider_receives_the_selected_supported_chain_id(monkeypatch):
    seen_chain_ids = []

    async def fake_goplus(chain_id, _address):
        seen_chain_ids.append(chain_id)
        return {}

    monkeypatch.setattr(chain_adapter.goplus, "get_token_security", fake_goplus)
    monkeypatch.setattr(chain_adapter.normalizer, "normalize", lambda raw: raw)

    for chain_id in (1, 8453, 196):
        raw, normalized = asyncio.run(chain_adapter.fetch_and_normalize("evm", chain_id, "0x1234567890123456789012345678901234567890"))
        assert raw == normalized == {}

    assert seen_chain_ids == ["1", "8453", "196"]


def test_solana_uses_the_separate_solana_provider(monkeypatch):
    called = False

    async def fake_solana(_address):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(chain_adapter.solana_goplus, "get_solana_token_security", fake_solana)
    monkeypatch.setattr(chain_adapter.solana_normalizer, "normalize_solana", lambda raw: raw)

    raw, normalized = asyncio.run(chain_adapter.fetch_and_normalize("solana", None, "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"))
    assert raw == normalized == {}
    assert called
