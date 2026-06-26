"""Account registration and authentication."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.user import User


class EmailTakenError(Exception):
    """Raised when registering an email that already exists."""


class WeakPasswordError(Exception):
    """Raised when the password is shorter than the minimum length."""


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def register(db: AsyncSession, email: str, password: str) -> User:
    if len(password) < settings.password_min_length:
        raise WeakPasswordError(
            f"La contraseña debe tener al menos {settings.password_min_length} caracteres."
        )
    normalized = _normalize_email(email)
    existing = await db.scalar(select(User).where(User.email == normalized))
    if existing is not None:
        raise EmailTakenError("Ese correo ya está registrado.")

    user = User(email=normalized, password_hash=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    """Return the user on valid credentials, else None (caller must not reveal why)."""
    normalized = _normalize_email(email)
    user = await db.scalar(select(User).where(User.email == normalized))
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
