"""Lightweight in-memory rate limiter.

Caps requests per client IP over a sliding window. Single-instance only (state
is per-process) — enough to stop a script from hammering the public API and
running up LLM cost. For multi-instance, swap the store for Redis.
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import settings

_WINDOW_SECONDS = 60.0
_hits: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # Railway/Vercel put the real client IP in X-Forwarded-For.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def rate_limit(request: Request) -> None:
    limit = settings.rate_limit_per_minute
    if limit <= 0:  # disabled
        return
    ip = _client_ip(request)
    now = time.monotonic()
    dq = _hits[ip]
    while dq and now - dq[0] > _WINDOW_SECONDS:
        dq.popleft()
    if len(dq) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes. Espera un momento e inténtalo de nuevo.",
        )
    dq.append(now)
