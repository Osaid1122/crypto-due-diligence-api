"""
GoPlus client for the Solana Token Security API (Beta).

Structurally different from the EVM client (goplus.py) in two ways, both
confirmed via live, authenticated testing against a real USDC-on-Solana
response (2026-07-19):

1. No chain_id — Solana is a single network, not a family of chain-ID-
   addressed EVM networks. This endpoint takes only a contract address.

2. Auth token goes in the `access_token` query parameter, not an
   `Authorization: Bearer` header. This was confirmed empirically by
   testing both approaches side by side against the same live token: the
   header approach returned `{"code":4012,"message":"signature
   verification failure"}` even after fixing the double-Bearer-prefix bug
   (see goplus_auth.py), while the query-param approach succeeded and
   returned the full live schema. This is a genuine GoPlus behavior
   difference between the EVM and Solana endpoints, not a client bug — the
   EVM endpoint's header approach was never contradicted by live testing,
   so goplus.py continues using it unchanged.

Address handling also differs from EVM: Solana addresses are case-sensitive
base58 (unlike EVM hex, which is case-insensitive), so this client does NOT
lowercase the address before sending it or looking it up in the response —
confirmed against the live response, which echoed the address back in
exactly the case it was sent.
"""

import httpx

from app.services.goplus_auth import get_access_token

BASE_URL = "https://api.gopluslabs.io/api/v1"


async def get_solana_token_security(address: str) -> dict:
    """
    Fetch raw Solana token security data from GoPlus for a given SPL mint
    address. Returns the raw per-token dict.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        token = await get_access_token(client)

        params = {"contract_addresses": address}
        if token:
            # Confirmed via live testing: query param, not Authorization
            # header — see module docstring.
            params["access_token"] = token

        resp = await client.get(f"{BASE_URL}/solana/token_security", params=params)
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("code") != 1:
            raise ValueError(f"GoPlus Solana error: {payload.get('message', 'unknown error')}")

        result = payload.get("result") or {}
        # Case-sensitive lookup first (confirmed correct against live data);
        # lowercase fallback kept only as a defensive no-op safety net, not
        # because it's expected to matter for Solana addresses.
        token_data = result.get(address) or result.get(address.lower())
        if not token_data:
            raise ValueError("No data returned for this Solana address. Check it's a valid SPL mint address.")

        return token_data
