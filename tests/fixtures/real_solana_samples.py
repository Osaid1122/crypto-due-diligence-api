"""Real GoPlus Solana Token Security response for USDC, captured via live
authenticated call on 2026-07-19 (see project history — validated through
scripts/validate_solana.py before that script was removed post-validation).
Used as a permanent regression fixture, same role as real_goplus_samples.py
plays for the EVM adapter."""

SOLANA_USDC = {
    "balance_mutable_authority": {"authority": [], "status": "0"},
    "closable": {"authority": [], "status": "0"},
    "creators": [],
    "default_account_state": "1",
    "default_account_state_upgradable": {"authority": [], "status": "0"},
    "dex": [
        {"dex_name": "orca", "tvl": "26300215.87", "lp_amount": None, "type": "Concentrated"},
        {"dex_name": "raydium", "tvl": "9977777.89", "lp_amount": "55052.494866193", "type": "Standard"},
        {"dex_name": "raydium", "tvl": "5918318.93", "lp_amount": None, "type": "Concentrated"},
        {"dex_name": "raydium", "tvl": "3802121.12", "lp_amount": None, "type": "Concentrated"},
        {"dex_name": "orca", "tvl": "1205379.59", "lp_amount": None, "type": "Concentrated"},
        {"dex_name": "raydium", "tvl": "522129.33", "lp_amount": "124303.607943", "type": "Standard"},
        {"dex_name": "raydium", "tvl": "411205.16", "lp_amount": None, "type": "Concentrated"},
        {"dex_name": "raydium", "tvl": "365865.81", "lp_amount": None, "type": "Concentrated"},
        {"dex_name": "orca", "tvl": "359289.16", "lp_amount": None, "type": "Concentrated"},
        {"dex_name": "raydium", "tvl": "332682.32", "lp_amount": None, "type": "Concentrated"},
    ],
    "freezable": {
        "authority": [{"address": "7dGbd2QZcCKcTndnHcTL8q7SMVXAkp688NTQYwrRCrar", "malicious_address": 0}],
        "status": "1",
    },
    "holder_count": "7348314",
    "holders": [
        {"account": "7VHUFJHWu2CuExkJcJrzhQPJ2oygupTWkL2A2For4BmE", "balance": "838122436.141969", "is_locked": 0, "percent": "0.1054"},
        {"account": "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9", "balance": "680028508.42226", "is_locked": 0, "percent": "0.0855"},
        {"account": "H8BgJgae6qhMtf7BM2JtddywSQt11WdxHHxkGLNX5hss", "balance": "279627240.277", "is_locked": 0, "percent": "0.0352"},
        {"account": "4Dg89gRmz8rUrTRiBP6XzfWJWtEuAxEYAWXn64AE3xvi", "balance": "165626874.347057", "is_locked": 0, "percent": "0.0208"},
        {"account": "AVzP2GeRmqGphJsMxWoqjpUifPpCret7LqWhD8NWQK49", "balance": "132536275.13695", "is_locked": 0, "percent": "0.0167"},
    ],
    "lp_holders": [],
    "metadata": {"description": "", "name": "USD Coin", "symbol": "USDC", "uri": ""},
    "metadata_mutable": {
        "metadata_upgrade_authority": [{"address": "2wmVCSfPxGPjrnMMn7rchp4uaeoTqN39mXFC2zhPdri9", "malicious_address": 0}],
        "status": "1",
    },
    "mintable": {
        "authority": [{"address": "BJE5MMbqXjVwjAF7oxwPYXnTXDyspzZyt4vwenNw5ruG", "malicious_address": 0}],
        "status": "1",
    },
    "non_transferable": "0",
    "total_supply": "7946037166.764042",
    "transfer_fee": {},
    "transfer_fee_upgradable": {"authority": [], "status": "0"},
    "transfer_hook": [],
    "transfer_hook_upgradable": {"authority": [], "status": "0"},
    "trusted_token": 1,
}


# Real GoPlus Solana Token Security response for TOES (TOESCOIN), a pump.fun
# token, captured via live authenticated call on 2026-08-08. Kept as a
# permanent regression fixture for the ECONOMIC signals (absolute TVL + 24h
# volume) and the severity-floor behaviour: its authorities are all clean
# (mint/freeze revoked, immutable, not closable) yet its liquidity is both
# concentrated (2 pools, ~100% share) AND economically dead ($12.51 total TVL,
# $0 24h volume). Before the economic signal + severity floor were added, this
# profile scored "Low" — the exact miscalibration these fixtures now guard
# against. Trimmed to the fields the normalizer/scoring engine consume; the
# per-pool `day/week/month.volume` shape is reproduced verbatim from the live
# response.
SOLANA_TOES = {
    "balance_mutable_authority": {"authority": [], "status": "0"},
    "closable": {"authority": [], "status": "0"},
    "creators": [],
    "default_account_state": "1",
    "default_account_state_upgradable": {"authority": [], "status": "0"},
    "dex": [
        {
            "dex_name": "raydium", "tvl": "12.51", "lp_amount": None, "type": "Concentrated",
            "day": {"price_max": "-1", "price_min": "-1", "volume": "0"},
            "week": {"price_max": "-1", "price_min": "-1", "volume": "0"},
            "month": {"price_max": "-1", "price_min": "-1", "volume": "0"},
        },
        {
            "dex_name": "raydium", "tvl": "0", "lp_amount": None, "type": "Concentrated",
            "day": {"price_max": "-1", "price_min": "-1", "volume": "0"},
            "week": {"price_max": "-1", "price_min": "-1", "volume": "0"},
            "month": {"price_max": "-1", "price_min": "-1", "volume": "0"},
        },
    ],
    "freezable": {"authority": [], "status": "0"},
    "holder_count": "19745",
    "holders": [
        {"account": "EE3zk9Fxp9guair2xeReFxf4TsEXeZFFuWETRna2PkcV", "balance": "24721032.54192", "is_locked": 0, "percent": "0.0247"},
        {"account": "AxzMpxZ4dPT9C9CKyijEQjL1NvSdFJ343PWZjsxZZvWr", "balance": "22780209.838111", "is_locked": 0, "percent": "0.0228"},
        {"account": "4AuNoqMnnQQPWad7PqdfbnYauAfxgdfJZyrHG5JDJeJi", "balance": "22593994.818931", "is_locked": 0, "percent": "0.0226"},
    ],
    "lp_holders": [],
    "metadata": {"description": "", "name": "TOES", "symbol": "TOESCOIN", "uri": "https://ipfs.io/ipfs/bafkreibj6kruv7q7fhojtbr4vih3tsvcyzje7qvnwxavtbihfm6gqxh4w4"},
    "metadata_mutable": {"metadata_upgrade_authority": [], "status": "0"},
    "mintable": {"authority": [], "status": "0"},
    "non_transferable": "0",
    "total_supply": "999944693.435886",
    "transfer_fee": {},
    "transfer_fee_upgradable": {"authority": [], "status": "0"},
    "transfer_hook": [],
    "transfer_hook_upgradable": {"authority": [], "status": "0"},
    "trusted_token": 0,
}
