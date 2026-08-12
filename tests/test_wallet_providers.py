"""Regression tests for wallet-data providers and their fallback orchestration.

These tests are the Phase 4A safety net. They lock in three things:

1. Centralized credentials — every provider reads its key/URL through
   app.core.config (not scattered os.getenv calls), and the ALCHEMY_API_KEY_ETH
   legacy alias keeps working.

2. Moralis -> Alchemy fallback — the bug fixed in Phase 4A. MoralisProvider used
   to swallow *every* request error (including the primary token-balances call)
   and return an empty-but-valid payload, so it always "succeeded" and the
   Alchemy fallback in fetch_wallet_portfolio was dead code. Now a hard failure
   of the primary request propagates and the orchestrator falls back to Alchemy.

3. Alchemy output contract — verified locally. NOTE: the Alchemy request/response
   *format* (endpoint shapes, param names, JSON keys) could not be verified
   against a captured Alchemy response — none exists in this repo and external
   docs were unavailable. These tests therefore assert only what is locally
   verifiable: given a response in the shape the current code reads, the returned
   payload conforms to the contract the wallet service/analyzer consume, and the
   provider is robust to empty/missing fields. They deliberately do NOT assert
   that the request shape matches Alchemy's real API.

No test makes a live network call: every HTTP boundary is monkeypatched.
Credentials are set/deleted explicitly per test (app.main.load_dotenv may have
populated os.environ with real keys), and no key value is ever printed.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from app.core import config
from app.services.wallet import providers


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

class _FakeResponse:
    """Minimal stand-in for httpx.Response — providers only call .json()."""

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def _fake_send(routes: dict):
    """Build a fake send_with_retry that dispatches by URL substring.

    ``routes`` maps a substring of the request URL to either a payload (returned
    as _FakeResponse.json()) or an Exception instance (raised, simulating a hard
    failure that survived the retry policy). The first matching substring wins.
    """

    async def _send(client, method, url, **kwargs):  # noqa: ANN001 - test stub
        for needle, result in routes.items():
            if needle in url:
                if isinstance(result, BaseException):
                    raise result
                return _FakeResponse(result)
        raise AssertionError(f"unexpected request to {url!r}")

    return _send


def _provider_class(*, payload=None, raises: BaseException | None = None, recorder: list | None = None, name: str = "stub"):
    """Return a WalletProvider-shaped class for orchestration tests."""

    class _Stub:
        async def fetch_wallet_data(self, chain_type, address):  # noqa: ANN001
            if recorder is not None:
                recorder.append(name)
            if raises is not None:
                raise raises
            return payload if payload is not None else {"metadata": {"provider": name}}

    return _Stub


EVM_ADDRESS = "0x1234567890123456789012345678901234567890"
SOLANA_ADDRESS = "FkbQZBcA4Z9XAoZTfSb1gG4FQAa1WUmfBcyG1xzqnsSB"


# ---------------------------------------------------------------------------
# 1. Centralized credentials (app.core.config)
# ---------------------------------------------------------------------------

def test_alchemy_key_prefers_primary_then_legacy_alias(monkeypatch):
    monkeypatch.setenv("ALCHEMY_API_KEY", "primary")
    monkeypatch.setenv("ALCHEMY_API_KEY_ETH", "legacy")
    assert config.alchemy_api_key() == "primary"

    monkeypatch.delenv("ALCHEMY_API_KEY", raising=False)
    assert config.alchemy_api_key() == "legacy"

    monkeypatch.delenv("ALCHEMY_API_KEY_ETH", raising=False)
    assert config.alchemy_api_key() == ""


def test_moralis_and_helius_keys_read_from_env(monkeypatch):
    monkeypatch.setenv("MORALIS_API_KEY", "m-key")
    monkeypatch.setenv("HELIUS_API_KEY", "h-key")
    assert config.moralis_api_key() == "m-key"
    assert config.helius_api_key() == "h-key"

    monkeypatch.delenv("MORALIS_API_KEY", raising=False)
    monkeypatch.delenv("HELIUS_API_KEY", raising=False)
    assert config.moralis_api_key() == ""
    assert config.helius_api_key() == ""


def test_provider_endpoint_urls_default_and_override(monkeypatch):
    for var in ("ALCHEMY_ETH_BASE_URL", "MORALIS_BASE_URL", "HELIUS_RPC_URL", "HELIUS_TRANSACTION_URL"):
        monkeypatch.delenv(var, raising=False)

    assert config.alchemy_eth_base_url() == config.ALCHEMY_ETH_BASE_URL_DEFAULT
    assert config.moralis_base_url() == config.MORALIS_BASE_URL_DEFAULT
    assert config.helius_rpc_url() == config.HELIUS_RPC_URL_DEFAULT
    assert config.helius_transaction_url() == config.HELIUS_TRANSACTION_URL_DEFAULT

    monkeypatch.setenv("ALCHEMY_ETH_BASE_URL", "https://proxy.example/v2")
    monkeypatch.setenv("MORALIS_BASE_URL", "https://proxy.example/moralis")
    assert config.alchemy_eth_base_url() == "https://proxy.example/v2"
    assert config.moralis_base_url() == "https://proxy.example/moralis"


# ---------------------------------------------------------------------------
# 2. Missing key -> the provider raises (so the fallback chain can proceed)
# ---------------------------------------------------------------------------

def test_alchemy_requires_key(monkeypatch):
    monkeypatch.delenv("ALCHEMY_API_KEY", raising=False)
    monkeypatch.delenv("ALCHEMY_API_KEY_ETH", raising=False)
    with pytest.raises(RuntimeError, match="Alchemy API key not configured"):
        asyncio.run(providers.AlchemyProvider().fetch_wallet_data("evm", EVM_ADDRESS))


def test_moralis_requires_key(monkeypatch):
    monkeypatch.delenv("MORALIS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Moralis API key not configured"):
        asyncio.run(providers.MoralisProvider().fetch_wallet_data("evm", EVM_ADDRESS))


def test_helius_requires_key(monkeypatch):
    monkeypatch.delenv("HELIUS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Helius API key not configured"):
        asyncio.run(providers.HeliusProvider().fetch_wallet_data("solana", SOLANA_ADDRESS))


def test_birdeye_provider_is_not_configured():
    with pytest.raises(RuntimeError, match="Birdeye provider not configured"):
        asyncio.run(providers.BirdeyeProvider().fetch_wallet_data("solana", SOLANA_ADDRESS))


# ---------------------------------------------------------------------------
# 3. The core Phase 4A bug fix: Moralis primary-request failure propagates
# ---------------------------------------------------------------------------

def test_moralis_token_request_failure_propagates(monkeypatch):
    """Regression: a hard failure of the PRIMARY token-balances request must
    raise (not be swallowed into an empty payload) so the orchestrator can fall
    back to Alchemy."""
    monkeypatch.setenv("MORALIS_API_KEY", "m-key")
    monkeypatch.setattr(
        providers,
        "send_with_retry",
        _fake_send({"/tokens": httpx.ConnectError("simulated network failure")}),
    )
    with pytest.raises(httpx.ConnectError):
        asyncio.run(providers.MoralisProvider().fetch_wallet_data("evm", EVM_ADDRESS))


def test_moralis_secondary_failures_stay_non_fatal(monkeypatch):
    """NFT and transaction failures degrade gracefully — a portfolio can still be
    scored from token balances alone, so those requests must NOT trigger the
    fallback."""
    monkeypatch.setenv("MORALIS_API_KEY", "m-key")
    routes = {
        "/tokens": {"result": [
            {"token_address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "balance": "5", "decimals": 6, "name": "Demo", "symbol": "DMO"},
        ]},
        "/nft": httpx.ConnectError("nft down"),
        # The bare "/{address}" transactions endpoint: matched by the address.
        EVM_ADDRESS: httpx.ConnectError("tx down"),
    }
    # Dispatch order matters: "/tokens" and "/nft" must be checked before the
    # address-only substring (which also appears in those URLs).
    ordered = {"/tokens": routes["/tokens"], "/nft": routes["/nft"], EVM_ADDRESS: routes[EVM_ADDRESS]}
    monkeypatch.setattr(providers, "send_with_retry", _fake_send(ordered))

    result = asyncio.run(providers.MoralisProvider().fetch_wallet_data("evm", EVM_ADDRESS))
    assert result["metadata"]["provider"] == "moralis"
    assert len(result["assets"]) == 1
    assert result["assets"][0]["address"] == "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert result["assets"][0]["chain_type"] == "evm"
    assert result["nft_count"] == 0
    assert result["transactions"] == []


def test_moralis_parses_token_balances(monkeypatch):
    monkeypatch.setenv("MORALIS_API_KEY", "m-key")
    ordered = {
        "/tokens": {"result": [
            {"token_address": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "balance": "1000", "decimals": 18, "name": "Tok", "symbol": "TOK"},
            {"balance": "1"},  # no contract -> skipped
        ]},
        "/nft": {"result": [{"a": 1}, {"b": 2}]},
        EVM_ADDRESS: {"result": [{"hash": "0xdead"}]},
    }
    monkeypatch.setattr(providers, "send_with_retry", _fake_send(ordered))

    result = asyncio.run(providers.MoralisProvider().fetch_wallet_data("evm", EVM_ADDRESS))
    assert [a["address"] for a in result["assets"]] == ["0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"]
    assert result["assets"][0]["chain_id"] == 1
    assert result["nft_count"] == 2
    assert result["transactions"] == [{"hash": "0xdead"}]


# ---------------------------------------------------------------------------
# 4. Alchemy output contract (locally verifiable only — see module docstring)
# ---------------------------------------------------------------------------

def test_alchemy_output_contract_shape(monkeypatch):
    monkeypatch.setenv("ALCHEMY_API_KEY", "a-key")
    routes = {
        "getTokenBalances": {"tokenBalances": [
            {"contractAddress": "0xcccccccccccccccccccccccccccccccccccccccc", "tokenBalance": "42", "name": "Coin", "symbol": "CN", "decimals": 8},
            {"tokenBalance": "9"},  # no contractAddress -> skipped
        ]},
        "getNFTs": {"totalCount": 3},
        "getAssetTransfers": {"transfers": [{"hash": "0x1"}, {"hash": "0x2"}]},
    }
    monkeypatch.setattr(providers, "send_with_retry", _fake_send(routes))

    result = asyncio.run(providers.AlchemyProvider().fetch_wallet_data("evm", EVM_ADDRESS))

    # Metadata identifies the provider used (consumers/UI rely on this).
    assert result["metadata"] == {"provider": "alchemy", "network": "ethereum"}
    # Asset shape matches what wallet/analyzer.py consumes.
    assert len(result["assets"]) == 1
    asset = result["assets"][0]
    assert asset["address"] == "0xcccccccccccccccccccccccccccccccccccccccc"
    assert asset["chain_type"] == "evm"
    assert asset["chain_id"] == 1
    assert asset["symbol"] == "CN"
    # balances mirror assets; transactions and nft_count pass through.
    assert result["balances"] == result["assets"]
    assert result["nft_count"] == 3
    assert result["transactions"] == [{"hash": "0x1"}, {"hash": "0x2"}]


def test_alchemy_robust_to_empty_responses(monkeypatch):
    monkeypatch.setenv("ALCHEMY_API_KEY", "a-key")
    routes = {"getTokenBalances": {}, "getNFTs": {}, "getAssetTransfers": {}}
    monkeypatch.setattr(providers, "send_with_retry", _fake_send(routes))

    result = asyncio.run(providers.AlchemyProvider().fetch_wallet_data("evm", EVM_ADDRESS))
    assert result["assets"] == []
    assert result["balances"] == []
    assert result["transactions"] == []
    assert result["nft_count"] == 0
    assert result["metadata"]["provider"] == "alchemy"


# ---------------------------------------------------------------------------
# 5. Fallback orchestration in fetch_wallet_portfolio
# ---------------------------------------------------------------------------

def test_evm_falls_back_to_alchemy_when_moralis_fails(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(providers, "MoralisProvider", _provider_class(raises=RuntimeError("moralis down"), recorder=calls, name="moralis"))
    monkeypatch.setattr(providers, "AlchemyProvider", _provider_class(payload={"metadata": {"provider": "alchemy"}}, recorder=calls, name="alchemy"))

    result = asyncio.run(providers.fetch_wallet_portfolio("evm", EVM_ADDRESS))
    assert result["metadata"]["provider"] == "alchemy"
    assert calls == ["moralis", "alchemy"]  # Moralis tried first, then Alchemy


def test_evm_uses_moralis_and_skips_alchemy_on_success(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(providers, "MoralisProvider", _provider_class(payload={"metadata": {"provider": "moralis"}}, recorder=calls, name="moralis"))
    monkeypatch.setattr(providers, "AlchemyProvider", _provider_class(raises=AssertionError("Alchemy must not be called"), recorder=calls, name="alchemy"))

    result = asyncio.run(providers.fetch_wallet_portfolio("evm", EVM_ADDRESS))
    assert result["metadata"]["provider"] == "moralis"
    assert calls == ["moralis"]


def test_evm_both_providers_fail_raises_runtimeerror(monkeypatch):
    monkeypatch.setattr(providers, "MoralisProvider", _provider_class(raises=RuntimeError("moralis down"), name="moralis"))
    monkeypatch.setattr(providers, "AlchemyProvider", _provider_class(raises=RuntimeError("alchemy down"), name="alchemy"))

    with pytest.raises(RuntimeError, match="No wallet provider could fetch data"):
        asyncio.run(providers.fetch_wallet_portfolio("evm", EVM_ADDRESS))


def test_solana_routes_to_helius(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(providers, "HeliusProvider", _provider_class(payload={"metadata": {"provider": "helius"}}, recorder=calls, name="helius"))
    monkeypatch.setattr(providers, "BirdeyeProvider", _provider_class(raises=AssertionError("Birdeye must not be called"), recorder=calls, name="birdeye"))

    result = asyncio.run(providers.fetch_wallet_portfolio("solana", SOLANA_ADDRESS))
    assert result["metadata"]["provider"] == "helius"
    assert calls == ["helius"]


def test_injected_provider_bypasses_the_default_chain():
    class _Injected:
        async def fetch_wallet_data(self, chain_type, address):  # noqa: ANN001
            return {"metadata": {"provider": "injected"}, "chain_type": chain_type}

    result = asyncio.run(providers.fetch_wallet_portfolio("evm", EVM_ADDRESS, provider=_Injected()))
    assert result["metadata"]["provider"] == "injected"
