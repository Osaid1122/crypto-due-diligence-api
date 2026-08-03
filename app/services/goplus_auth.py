"""
Shared GoPlus authentication handshake — used by both the EVM adapter
(goplus.py) and the Solana adapter (solana_goplus.py). Both hit the same
POST /api/v1/token endpoint with the same SHA1(app_key + time + app_secret)
signed handshake (docs.gopluslabs.io/reference/getaccesstokenusingpost).

ROOT CAUSE FIX — confirmed via live testing, 2026-07-19:
The access_token GoPlus returns already contains a literal "Bearer " prefix
baked into the string itself, e.g.:
    "access_token": "Bearer eyJhY2NvdW50SWQiOjY5NzAs..."
This isn't documented anywhere. The original code built
`Authorization: Bearer {token}` from that value, producing a double-prefixed
header ("Bearer Bearer ..."), which GoPlus's signature check correctly
rejected with `{"code":4012,"message":"signature verification failure"}`.
This was a client-side bug, not a GoPlus outage or invalid credentials —
confirmed by fixing the prefix and successfully retrieving a full live
Solana response for USDC. `_strip_bearer_prefix()` below guards against it
for both chains, since the EVM path carried the identical latent bug (never
exercised with real credentials in this project before now — EVM's
unauthenticated tier was sufficient for all prior testing).

SEPARATE Solana-specific quirk (this one IS a real GoPlus behavior, not a
client bug): the Solana Token Security endpoint accepts the token as an
`access_token` query parameter but rejects it via the documented
`Authorization: Bearer` header with the same 4012 error, even with the
double-prefix bug fixed. Confirmed by testing both approaches side by side
against the same live token. The EVM endpoint continues using the header
approach as originally implemented (its documented behavior was never
contradicted by live testing) — see solana_goplus.py for where the two
diverge.
"""

import hashlib
import time
import httpx

from app.core.config import get_settings
from app.services.retry import send_with_retry

TOKEN_URL = "https://api.gopluslabs.io/api/v1/token"


def _strip_bearer_prefix(token: str) -> str:
    """Defensively remove a literal 'Bearer ' prefix if GoPlus already
    included one in the token value — see module docstring."""
    if token.startswith("Bearer "):
        return token[len("Bearer "):]
    return token


async def get_access_token(client: httpx.AsyncClient) -> str | None:
    """
    Returns a clean access token (guaranteed no 'Bearer ' prefix, regardless
    of whether GoPlus included one), or None if no credentials are
    configured. Both the EVM and Solana token_security endpoints work
    unauthenticated at reasonable request volume, so this is optional for
    both adapters, not required.
    """
    settings = get_settings()
    if not settings.goplus_app_key or not settings.goplus_app_secret:
        return None

    ts = str(int(time.time()))
    raw = f"{settings.goplus_app_key}{ts}{settings.goplus_app_secret}"
    sign = hashlib.sha1(raw.encode()).hexdigest()

    resp = await send_with_retry(
        client,
        "POST",
        TOKEN_URL,
        json={
            "app_key": settings.goplus_app_key,
            "time": ts,
            "sign": sign,
        },
    )
    data = resp.json()
    token = data.get("result", {}).get("access_token")
    return _strip_bearer_prefix(token) if token else None
