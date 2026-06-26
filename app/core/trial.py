"""Trial logic (Fase 2).

The trial window is derived from the user's `created_at` — no separate table.
A user has full access for `settings.trial_days` days after registration.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.models.user import User


@dataclass
class TrialStatus:
    active: bool
    days_remaining: int
    expires_at: datetime


def ensure_trial_active(user: User | None) -> None:
    """Raise HTTP 402 if an authenticated user's trial has expired.

    Anonymous users (user is None) are not subject to the trial.
    """
    if user is None:
        return
    if not trial_status(user).active:
        from fastapi import HTTPException, status  # noqa: PLC0415

        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "Tu período de prueba ha terminado. "
                f"Escríbenos a {settings.trial_contact_email} para seguir usando DocuSeguro."
            ),
        )


def trial_status(user: User) -> TrialStatus:
    created = user.created_at
    # Guard against naive datetimes (SQLite in tests stores tz-naive).
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    expires_at = created + timedelta(days=settings.trial_days)
    now = datetime.now(UTC)
    remaining = expires_at - now
    days_remaining = max(0, remaining.days + (1 if remaining.seconds > 0 else 0))
    return TrialStatus(
        active=now < expires_at,
        days_remaining=days_remaining if now < expires_at else 0,
        expires_at=expires_at,
    )
