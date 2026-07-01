from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import models so Base.metadata includes all tables
import app.models.doc_pii_token  # noqa: F401
import app.models.document  # noqa: F401
import app.models.pii_token  # noqa: F401
import app.models.query_cache  # noqa: F401
import app.models.query_log  # noqa: F401
import app.models.user  # noqa: F401
from app.core.config import settings
from app.models.base import Base

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        yield session
