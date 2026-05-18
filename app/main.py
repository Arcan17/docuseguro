from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from sqlalchemy import delete

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.models.database import AsyncSessionLocal, create_tables
from app.models.pii_token import PIIToken

configure_logging(settings.log_level)
logger = get_logger(__name__)

_scheduler = AsyncIOScheduler()


async def _cleanup_expired_pii() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(PIIToken).where(PIIToken.expires_at < datetime.now(UTC))
        )
        await db.commit()
        if result.rowcount:
            logger.info("pii_cleanup", deleted=result.rowcount)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("startup", provider=settings.llm_provider, log_level=settings.log_level)

    await create_tables()
    logger.info("db_tables_ready")

    _scheduler.add_job(_cleanup_expired_pii, "interval", minutes=30, id="pii_cleanup")
    _scheduler.start()
    logger.info("scheduler_started")

    yield

    _scheduler.shutdown(wait=False)
    logger.info("shutdown_complete")


app = FastAPI(
    title="PrivRAG",
    description="Privacy-preserving RAG pipeline for enterprise documents",
    version="0.1.0",
    lifespan=lifespan,
)

from app.api.routers import health, ingest, metrics, query, webhook  # noqa: E402

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(webhook.router)
app.include_router(metrics.router)
