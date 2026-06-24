import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.base import Base


@pytest.fixture(autouse=True)
def _disable_rate_limit():
    """Rate limiting is per-IP in-memory; all tests share one client IP, so it
    would trip spuriously. Disable it during tests (it's verified separately)."""
    from app.core import rate_limit as rl
    from app.core.config import settings

    old = settings.rate_limit_per_minute
    settings.rate_limit_per_minute = 0
    rl._hits.clear()
    yield
    settings.rate_limit_per_minute = old


@pytest.fixture(scope="function")
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
