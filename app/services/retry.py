"""
Shared retry policy for outbound provider HTTP calls.

All external provider requests (GoPlus EVM/Solana, the GoPlus auth handshake,
and the wallet data providers — Alchemy, Moralis, Helius) go through
`send_with_retry`, which retries transient failures only:

  * network-level errors (httpx.RequestError: connect/read/timeout/etc.)
  * HTTP 5xx responses
  * HTTP 429 (rate limited)

It deliberately does NOT retry 4xx client errors (e.g. an invalid address or a
malformed request), which are not going to succeed on a second identical call.

3 attempts total with exponential backoff. `reraise=True` means the original
httpx exception propagates after the final attempt, so existing callers that
catch httpx.HTTPStatusError / ValueError keep working unchanged.
"""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)


def _is_retryable(exc: BaseException) -> bool:
    """Retry transient failures only — never 4xx client errors."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status == 429 or status >= 500
    if isinstance(exc, httpx.RequestError):
        return True
    return False


# Reusable decorator for provider-call functions. reraise=True keeps the
# original exception type after exhausting attempts.
provider_retry = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=8),
    retry=retry_if_exception(_is_retryable),
)


@provider_retry
async def send_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    """
    Issue an httpx request and raise for status, retrying only on transient
    failures (network errors, 5xx, 429). 4xx responses raise immediately and
    are not retried. Returns the successful response.
    """
    resp = await client.request(method, url, **kwargs)
    resp.raise_for_status()
    return resp
