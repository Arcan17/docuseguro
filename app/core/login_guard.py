"""Per-account login lockout to slow down brute-force guessing.

Complements the per-IP rate limiter: even from many IPs, repeated failures
against the *same account* trigger a temporary cooldown. In-memory, single
process — for multi-instance, back this with a shared store (e.g. Redis).
Keyed by the submitted email regardless of whether it exists, so it never
reveals whether an account is real.
"""
import time

from app.core.config import settings

_failures: dict[str, list[float]] = {}


def _recent(email: str) -> list[float]:
    now = time.monotonic()
    window = settings.login_lockout_seconds
    fresh = [t for t in _failures.get(email, []) if now - t < window]
    _failures[email] = fresh
    return fresh


def is_locked(email: str) -> bool:
    return len(_recent(email)) >= settings.login_max_failures


def record_failure(email: str) -> None:
    _failures.setdefault(email, []).append(time.monotonic())


def clear(email: str) -> None:
    _failures.pop(email, None)
