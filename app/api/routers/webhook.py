import uuid as uuid_module
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_api_key
from app.core.logging import get_logger
from app.models.database import get_db
from app.models.query_log import QueryLog

logger = get_logger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


class CRMWebhookPayload(BaseModel):
    query_hash: str
    latency_ms: int
    cache_hit: bool
    chunk_count: int
    source: str = "privrag"


class CRMWebhookResponse(BaseModel):
    status: str
    received_at: datetime


@router.post("/crm", response_model=CRMWebhookResponse, dependencies=[Depends(require_api_key)])
async def receive_crm_event(
    payload: CRMWebhookPayload,
    db: AsyncSession = Depends(get_db),
) -> CRMWebhookResponse:
    log = QueryLog(
        session_id=uuid_module.uuid4(),
        query_hash=payload.query_hash,
        cache_hit=payload.cache_hit,
        chunk_count=payload.chunk_count,
        latency_ms=payload.latency_ms,
        llm_provider="webhook",
    )
    db.add(log)
    await db.commit()

    logger.info(
        "crm_event_received",
        cache_hit=payload.cache_hit,
        latency_ms=payload.latency_ms,
        source=payload.source,
    )
    return CRMWebhookResponse(status="ok", received_at=datetime.now(UTC))
