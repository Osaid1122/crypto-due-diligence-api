"""
Client for GoPlus Security's Token Security API.

The token_security endpoint is GoPlus's free/permissionless tier and works
without authentication at reasonable request volumes. If you start hitting
401s or rate limits, sign up at https://console.gopluslabs.io, grab an
app_key + app_secret, and set GOPLUS_APP_KEY / GOPLUS_APP_SECRET in .env —
then swap in the authenticated path below.
"""

import hashlib
import time
import httpx

from app.core.config import get_settings

BASE_URL = "https://api.gopluslabs.io/api/v1"


async def _get_access_token(client: httpx.AsyncClient) -> str | None:
    """Exchange app_key + app_secret for a short-lived access token.
    Only needed if you're hitting rate limits on the unauthenticated tier."""
    settings = get_settings()
    if not settings.goplus_app_key or not settings.goplus_app_secret:
        return None

    ts = str(int(time.time()))
    raw = f"{settings.goplus_app_key}{ts}{settings.goplus_app_secret}"
    sign = hashlib.sha1(raw.encode()).hexdigest()

    resp = await client.post(
        f"{BASE_URL}/token",
        json={
            "app_key": settings.goplus_app_key,
            "time": ts,
            "sign": sign,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("result", {}).get("access_token")


async def get_token_security(chain_id: str, address: str) -> dict:
    """
    Fetch raw token security data from GoPlus for a given chain + contract address.
    Returns the raw `result` dict from GoPlus, keyed by lowercase address.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        headers = {}
        token = await _get_access_token(client)
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
