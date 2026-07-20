"""
Client for GoPlus Security's EVM Token Security API.

The token_security endpoint is GoPlus's free/permissionless tier and works
without authentication at reasonable request volumes. If you start hitting
401s or rate limits, sign up at https://console.gopluslabs.io, grab an
app_key + app_secret, and set GOPLUS_APP_KEY / GOPLUS_APP_SECRET in .env —
the authenticated path below (get_access_token) then activates automatically.

Auth handshake lives in goplus_auth.py, shared with the Solana adapter —
see that module's docstring for a real bug found and fixed during Solana
validation (2026-07-19) that also applied here, silently, the whole time.
"""

import httpx

from app.services.goplus_auth import get_access_token

BASE_URL = "https://api.gopluslabs.io/api/v1"


async def get_token_security(chain_id: str, address: str) -> dict:
    """
    Fetch raw token security data from GoPlus for a given chain + contract address.
    Returns the raw `result` dict from GoPlus, keyed by lowercase address.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        headers = {}
        token = await get_access_token(client)
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = await client.get(
            f"{BASE_URL}/token_security/{chain_id}",
            params={"contract_addresses": address.lower()},
            headers=headers,
        )
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("code") != 1:
            raise ValueError(f"GoPlus error: {payload.get('message', 'unknown error')}")

        result = payload.get("result", {})
        token_data = result.get(address.lower())
        if not token_data:
            raise ValueError("No data returned for this address. Check the address and chain_id.")

        return token_data
