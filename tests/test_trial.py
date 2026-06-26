"""Tests para la lógica de trial (Fase 2)."""
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.core.trial import ensure_trial_active, trial_status
from app.models.user import User


def _user(days_ago: float) -> User:
    u = User(email="x@y.cl", password_hash="h")
    u.created_at = datetime.now(UTC) - timedelta(days=days_ago)
    return u


def test_trial_active_for_new_user() -> None:
    status = trial_status(_user(0))
    assert status.active is True
    assert status.days_remaining == 14


def test_trial_active_midway() -> None:
    status = trial_status(_user(10))
    assert status.active is True
    assert 1 <= status.days_remaining <= 4


def test_trial_expired_after_window() -> None:
    status = trial_status(_user(15))
    assert status.active is False
    assert status.days_remaining == 0


def test_ensure_trial_active_allows_anonymous() -> None:
    # No user (anonymous) is never blocked.
    ensure_trial_active(None)


def test_ensure_trial_active_allows_active_user() -> None:
    ensure_trial_active(_user(1))


def test_ensure_trial_active_blocks_expired_user() -> None:
    with pytest.raises(HTTPException) as exc:
        ensure_trial_active(_user(20))
    assert exc.value.status_code == 402
