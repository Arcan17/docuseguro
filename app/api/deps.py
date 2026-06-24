from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.models.database import get_db
from app.models.user import User
from app.services.cache.query_cache import CacheService
from app.services.rag_pipeline import RAGPipeline

_bearer = HTTPBearer(auto_error=False)


async def get_cache_service(
    db: AsyncSession = Depends(get_db),
) -> CacheService:
    return CacheService(db)


async def get_rag_pipeline(
    db: AsyncSession = Depends(get_db),
) -> RAGPipeline:
    return RAGPipeline(db)


async def _user_from_token(
    creds: HTTPAuthorizationCredentials | None, db: AsyncSession
) -> User | None:
    if creds is None:
        return None
    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        return None
    return await db.get(User, user_id)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Require a valid Bearer token. Raises 401 otherwise."""
    user = await _user_from_token(creds, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Return the user if a valid token is present, else None (anonymous mode)."""
    return await _user_from_token(creds, db)
