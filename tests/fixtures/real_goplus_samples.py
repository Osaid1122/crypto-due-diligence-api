"""Real GoPlus responses captured on 2026-07-10 for USDC, LINK, UNI (Ethereum mainnet).
Used to validate normalizer.py and scoring.py against actual API shape, not assumptions."""

USDC = {
    "buy_tax": "0", "creator_address": "0x95ba4cf87d6723ad9c0db21737d862be80e93911",
    "creator_balance": "2505.454092", "creator_percent": "0.000000",
    "holder_count": "7947459",
    "holders": [
        {"address": "0x37305b1cd40574e4c5ce33f8e8306be057fd7341", "is_contract": 0, "percent": "0.086560314585059403", "is_locked": 0},
        {"address": "0xe1940f578743367f38d3f25c2d2d32d6636929b6", "is_contract": 1, "percent": "0.033557395600250997", "is_locked": 0},
    ],
    "is_honeypot": "0", "is_in_dex": "1", "is_open_source": "1", "is_proxy": "1",
    "sell_tax": "0", "token_name": "USD Coin", "token_symbol": "USDC",
    "total_supply": "50659473675.807594", "cannot_buy": "0", "trust_list": "1",
    # NOTE: no is_mintable, cannot_sell_all, hidden_owner, lp_holders — genuinely absent
}

LINK = {
    "can_take_back_ownership": "0", "cannot_buy": "0", "cannot_sell_all": "0",
    "creator_percent": "0.000000",
    "hidden_owner": "0", "is_blacklisted": "0", "is_honeypot": "0",
    "is_mintable": "0", "is_open_source": "1", "is_proxy": "0",
    "owner_balance": "0", "owner_percent": "0",
    "selfdestruct": "0", "token_name": "ChainLink Token", "token_symbol": "LINK",
    "trading_cooldown": "0", "trust_list": "1",
    "holder_count": "905720",
    "holders": [
        {"address": "0xf977814e90da44bfa03b6295a0616a897441acec", "is_contract": 0, "percent": "0.055000000000000000", "is_locked": 0},
        {"address": "0xbc10f2e862ed4502144c7d632a3459f49dfcdb5e", "is_contract": 1, "percent": "0.040875543636950000", "is_locked": 0},
    ],
    "lp_holder_count": "186",
    # 10+ genuinely distinct LP positions, none individually locked — fragmented, not risky
    "lp_holders": [
        {"address": "0x72655b3926db3afbe914a53b0604905af7ce11a5", "percent": "0.527381796572326308", "is_locked": 0},
        {"address": "0x319e4a395a5a232e6d3d9230fa1b6b287f4ea165", "percent": "0.066796264587167495", "is_locked": 0},
        {"address": "0xfcba81c19b20d2f2d7cea6e10647803ede7697c0", "percent": "0.052715715609690663", "is_locked": 0},
        {"address": "0x3207dc41ce2aa11cf4aac48499b36c75ae328908", "percent": "0.049565768995871747", "is_locked": 0},
        {"address": "0xd14f57283d1487f7bec9a3b4ccfed80930bbc91c", "percent": "0.048948842495835443", "is_locked": 0},
        {"address": "0x44459fd21383e58b33b446d06af829bc0d95c342", "percent": "0.037520728766989200", "is_locked": 0},
        {"address": "0xc4ef73713cbeaffd7862b5d4851f512e7f290c47", "percent": "0.030030773135849307", "is_locked": 0},
        {"address": "0x72f002e3332ab46a90ea2ef6238a083938519083", "percent": "0.024950746401411276", "is_locked": 0},
        {"address": "0x5310538e6ed133ac2a276ba467422de1aacaba66", "percent": "0.018503592395042359", "is_locked": 0},
        {"address": "0x6bb32460b408aa03d0ee60fc8fbfe9f7ef9d2339", "percent": "0.014494704075054872", "is_locked": 0},
    ],
}

UNI = {
    "can_take_back_ownership": "0", "hidden_owner": "0", "is_blacklisted": "0",
    "is_honeypot": "0", "is_mintable": "0", "is_open_source": "1", "is_proxy": "0",
    "owner_address": "0x1a9c8182c09f50c8318d769245bea52c32be35bc",
    "owner_percent": "0.272135", "selfdestruct": "0", "token_name": "Uniswap",
    "token_symbol": "UNI", "trading_cooldown": "0", "trust_list": "1", "cannot_buy": "0",
    "holder_count": "387676",
    "holders": [
        {"address": "0x1a9c8182c09f50c8318d769245bea52c32be35bc", "is_contract": 1, "percent": "0.272134858479070410", "is_locked": 0},
        {"address": "0x000000000000000000000000000000000000dead", "is_contract": 0, "percent": "0.106877579967052124", "is_locked": 1},
        {"address": "0x61cb39bece033c5bda281747db1c15cced2096eb", "is_contract": 0, "percent": "0.023047480513298522", "is_locked": 0},
    ],
    # no lp_holders field returned at all for UNI in this snapshot
}
