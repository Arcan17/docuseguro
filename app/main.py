from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


async def _cleanup_expired_uploads() -> None:
    from app.services.vector_store import delete_expired_uploads  # noqa: PLC0415

    await delete_expired_uploads(settings.upload_ttl_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("startup", provider=settings.llm_provider, log_level=settings.log_level)

    await create_tables()
    logger.info("db_tables_ready")

    # Warm the embedding model inside the web process. It loads lazily via an
    # lru_cache on first use, and the startup seed runs in a separate process,
    # so without this the FIRST user query pays the multi-second model load.
    try:
        from app.services.ingestion.embedder import embed_query  # noqa: PLC0415

        await embed_query("warmup")
        logger.info("embedding_model_warmed")
    except Exception as exc:  # never block startup on warmup
        logger.warning("embedding_warmup_failed", error=str(exc))

    _scheduler.add_job(_cleanup_expired_pii, "interval", minutes=30, id="pii_cleanup")
    _scheduler.add_job(
        _cleanup_expired_uploads, "interval", minutes=10, id="upload_cleanup"
    )
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routers import health, ingest, metrics, query, webhook  # noqa: E402

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(webhook.router)
app.include_router(metrics.router)
