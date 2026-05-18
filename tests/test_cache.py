import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.services.cache.query_cache import CacheService, make_cache_key


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


def test_make_cache_key_deterministic() -> None:
    k1 = make_cache_key("¿Qué es la política de vacaciones?", "contexto A")
    k2 = make_cache_key("¿Qué es la política de vacaciones?", "contexto A")
    assert k1 == k2


def test_make_cache_key_differs_on_query() -> None:
    k1 = make_cache_key("query A", "context")
    k2 = make_cache_key("query B", "context")
    assert k1 != k2


def test_make_cache_key_differs_on_context() -> None:
    k1 = make_cache_key("query", "context A")
    k2 = make_cache_key("query", "context B")
    assert k1 != k2


async def test_cache_miss_returns_none(db_session: AsyncSession) -> None:
    svc = CacheService(db_session)
    result = await svc.get("nonexistent_key")
    assert result is None


async def test_set_and_get(db_session: AsyncSession) -> None:
    svc = CacheService(db_session)
    key = make_cache_key("¿Cuáles son los beneficios?", "contexto de beneficios")
    await svc.set(key, "Los beneficios incluyen seguro médico.")
    result = await svc.get(key)
    assert result == "Los beneficios incluyen seguro médico."


async def test_get_increments_hit_count(db_session: AsyncSession) -> None:
    from sqlalchemy import select

    from app.models.query_cache import QueryCache

    svc = CacheService(db_session)
    key = make_cache_key("pregunta repetida", "contexto")
    await svc.set(key, "respuesta")

    await svc.get(key)
    await svc.get(key)

    row = await db_session.scalar(select(QueryCache).where(QueryCache.cache_key == key))
    assert row is not None
    assert row.hit_count == 2
