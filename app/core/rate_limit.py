"""
Shared slowapi rate limiter.

Kept in its own module so the routers can import the `limiter` instance to
decorate their endpoints while `app.main` wires up the middleware and error
handler — importing it from `main` would create a circular import (main imports
the routers).

The per-IP default is deliberately conservative: GoPlus's own free tier caps at
30 calls/min, and a single wallet scan can fan out into many per-asset GoPlus
calls, so we keep clients well under that ceiling.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Per-IP limit applied to the analysis endpoints.
ANALYZE_RATE_LIMIT = "20/minute"

limiter = Limiter(key_func=get_remote_address)
