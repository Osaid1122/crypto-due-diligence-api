import asyncio

from app.services.wallet import service as wallet_service
from app.services.wallet.scoring import build_portfolio_score
from app.services.wallet.summary import build_summary
from app.services.wallet.service import analyze_wallet


def test_empty_wallet_analysis_explains_live_data_gap():
    async def fake_provider(chain_type, address):
        return {
            "assets": [],
            "error": "No wallet assets could be fetched from the configured provider.",
        }

    report = asyncio.run(analyze_wallet("0x1234567890123456789012345678901234567890", chain_type="evm", provider=fake_provider))

    assert report["status"] == "empty"
    assert report["portfolio_score"] == 0
    assert "No live wallet assets" in report["summary"]
    assert report["timeline"][-1]["step"] == "Analysis completed"


def test_wallet_analysis_aggregates_live_metrics_from_provider(monkeypatch):
    async def fake_default_provider(chain_type, address):
        return {
            "assets": [
                {
                    "address": "0x1111111111111111111111111111111111111111",
                    "chain_type": "evm",
                    "chain_id": 1,
                    "name": "Demo Token",
                    "symbol": "DMT",
                    "balance": "1000000000000000000",
                    "decimals": 18,
                }
            ],
            "nft_count": 3,
            "transactions": [{"hash": "0xabc"}],
            "balances": [{"address": "0x1111111111111111111111111111111111111111", "balance": "1000000000000000000"}],
            "metadata": {"wallet_name": "demo"},
            "error": None,
        }

    async def fake_fetch_and_normalize(chain_type, chain_id, address):
        return {"audit": False, "is_open_source": True}, {"token_name": "Demo Token", "token_symbol": "DMT", "trust_list": True}

    monkeypatch.setattr(wallet_service, "_default_provider", fake_default_provider)
    monkeypatch.setattr(wallet_service.analyze_assets.__globals__["chain_adapter"], "fetch_and_normalize", fake_fetch_and_normalize)

    report = asyncio.run(analyze_wallet("0x1234567890123456789012345678901234567890", chain_type="evm"))

    assert report["status"] == "success"
    assert report["detail_metrics"]["asset_count"] == 1
    assert report["detail_metrics"]["nft_count"] == 3
    assert report["detail_metrics"]["transaction_count"] == 1
    assert report["assets"][0]["name"] == "Demo Token"


def test_portfolio_scoring_excludes_none_but_preserves_zero_score():
    score = build_portfolio_score([
        {"name": "Verified zero-risk score", "risk_score": 0, "has_audit": True},
        {"name": "Unavailable", "risk_score": None, "analysis_status": "unavailable"},
    ])

    assert score["score"] == 100
    assert score["detail_metrics"]["average_token_risk"] == 0
    assert score["risk_breakdown"][0]["value"] == 1


def test_all_unscored_assets_have_no_portfolio_score_or_false_safe_summary():
    assets = [
        {"name": "Native SOL", "risk_score": None, "analysis_status": "not_applicable"},
        {"name": "Unavailable SPL", "risk_score": None, "analysis_status": "unavailable"},
    ]
    score = build_portfolio_score(assets)
    summary = build_summary(assets, score, {"provider": "helius"})

    assert score["score"] is None
    assert score["risk_level"] == "Unknown"
    assert "remain unscored" in summary
    assert "looks clear" not in summary


def test_wallet_flows_keep_nullable_scores_safe_for_evm_xlayer_and_solana(monkeypatch):
    async def fake_analyze_assets(_assets):
        return [
            {"name": "Scored", "risk_score": 45, "risk_level": "Medium", "has_audit": False},
            {"name": "Unavailable", "risk_score": None, "risk_level": "Unscored", "analysis_status": "unavailable", "has_audit": False},
        ]

    async def fake_provider(chain_type, _address):
        return {"assets": [{"address": "asset"}], "transactions": [], "balances": [], "metadata": {"provider": "test", "network": chain_type}}

    monkeypatch.setattr(wallet_service, "analyze_assets", fake_analyze_assets)

    cases = [
        ("evm", "0x1234567890123456789012345678901234567890"),
        ("xlayer", "0x1234567890123456789012345678901234567890"),
        ("solana", "FkbQZBcA4Z9XAoZTfSb1gG4FQAa1WUmfBcyG1xzqnsSB"),
    ]
    for chain_type, address in cases:
        report = asyncio.run(analyze_wallet(address, chain_type=chain_type, provider=fake_provider))
        assert report["status"] == "success"
        assert report["chain_type"] == chain_type
        assert report["portfolio_score"] == 55
        assert report["assets"][1]["risk_score"] is None
