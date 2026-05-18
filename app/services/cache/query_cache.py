import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.query_cache import QueryCache


def make_cache_key(query_text: str, context_str: str) -> str:
    """SHA256 of query + sorted context to produce a stable cache key."""
    raw = query_text.strip() + "\n---\n" + context_str
    return hashlib.sha256(raw.encode()).hexdigest()


class CacheService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, cache_key: str) -> str | None:
        now = datetime.now(UTC)
        row = await self._db.scalar(
            select(QueryCache).where(
                QueryCache.cache_key == cache_key,
                QueryCache.expires_at > now,
            )
        )
        if row is None:
            return None

        await self._db.execute(
            update(QueryCache)
            .where(QueryCache.cache_key == cache_key)
            .values(hit_count=QueryCache.hit_count + 1)
        )
        await self._db.commit()
        return row.response

    async def set(self, cache_key: str, response: str) -> None:
        ttl = settings.cache_ttl_seconds
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)

        entry = QueryCache(
            cache_key=cache_key,
            response=response,
            expires_at=expires_at,
        )
        self._db.add(entry)
        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            # Already exists (race condition) — update instead
            await self._db.execute(
                update(QueryCache)
                .where(QueryCache.cache_key == cache_key)
                .values(response=response, expires_at=expires_at)
            )
            await self._db.commit()
