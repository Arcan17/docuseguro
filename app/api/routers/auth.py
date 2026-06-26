from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    StatsResponse,
    UserResponse,
)
from app.core import login_guard
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token
from app.core.trial import trial_status
from app.models.database import get_db
from app.models.document import Document
from app.models.query_log import QueryLog
from app.models.user import User
from app.services import auth_service
from app.services.vector_store import delete_by_owner

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit)],
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    try:
        user = await auth_service.register(db, body.email, body.password)
    except auth_service.WeakPasswordError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except auth_service.EmailTakenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return AuthResponse(access_token=create_access_token(user.id), email=user.email)


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(rate_limit)])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    key = body.email.strip().lower()
    if login_guard.is_locked(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Espera unos minutos.",
        )
    user = await auth_service.authenticate(db, body.email, body.password)
    if user is None:
        login_guard.record_failure(key)
        # Generic message — never reveal whether the email exists.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )
    login_guard.clear(key)
    return AuthResponse(access_token=create_access_token(user.id), email=user.email)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email)


@router.get("/stats", response_model=StatsResponse)
async def stats(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> StatsResponse:
    ts = trial_status(user)
    docs = await db.scalar(
        select(func.count()).select_from(Document).where(Document.user_id == user.id)
    )
    queries = await db.scalar(
        select(func.count()).select_from(QueryLog).where(QueryLog.user_id == user.id)
    )
    pii_events = await db.scalar(
        select(func.count())
        .select_from(QueryLog)
        .where(QueryLog.user_id == user.id, QueryLog.pii_found.is_(True))
    )
    return StatsResponse(
        email=user.email,
        trial_active=ts.active,
        trial_days_remaining=ts.days_remaining,
        trial_expires_at=ts.expires_at.isoformat(),
        documents_count=docs or 0,
        queries_count=queries or 0,
        pii_events_count=pii_events or 0,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    # Stateless JWT: the client discards the token. Nothing to do server-side.
    return None


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    await delete_by_owner(f"user:{user.id}")
    await db.execute(delete(Document).where(Document.user_id == user.id))
    await db.delete(user)
    await db.commit()
    return None
