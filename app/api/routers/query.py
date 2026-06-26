import hashlib
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.api.schemas.query import QueryRequest, QueryResponse, SourceChunk
from app.core.auth import require_api_key
from app.core.rate_limit import rate_limit
from app.core.trial import ensure_trial_active
from app.models.database import get_db
from app.models.user import User
from app.services.rag_pipeline import RAGPipeline

router = APIRouter(prefix="/query", tags=["query"])


@router.post(
    "/stream",
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
async def query_stream(
    request: QueryRequest,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    ensure_trial_active(user)
    owner = f"user:{user.id}" if user is not None else request.session_id
    pipeline = RAGPipeline(db)

    async def event_stream():
        async for event in pipeline.query_stream(
            session_id=request.session_id, query_text=request.query, owner=owner
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "",
    response_model=QueryResponse,
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
async def query_documents(
    request: QueryRequest,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    # Authenticated users with an expired trial are blocked (anonymous users pass).
    ensure_trial_active(user)
    # Search is scoped to this owner: the account if authenticated, else the
    # anonymous browser session.
    owner = f"user:{user.id}" if user is not None else request.session_id
    pipeline = RAGPipeline(db)
    result = await pipeline.query(
        session_id=request.session_id,
        query_text=request.query,
        owner=owner,
    )

    source_chunks = [
        SourceChunk(
            chunk_id=c.chunk_id,
            doc_id=c.doc_id,
            similarity=round(c.similarity, 4),
            text_preview=c.text[:120] + "..." if len(c.text) > 120 else c.text,
        )
        for c in result.chunks
    ]

    # Fire workflow notifications (non-blocking)
    import asyncio  # noqa: PLC0415

    from app.services.crm_service import log_crm_event  # noqa: PLC0415
    from app.services.telegram_service import notify_query  # noqa: PLC0415

    asyncio.create_task(
        notify_query(
            clean_query=result.clean_query,
            latency_ms=result.latency_ms,
            cache_hit=result.cache_hit,
            pii_found=result.pii_found,
            pii_types=result.pii_types,
        )
    )
    asyncio.create_task(
        log_crm_event(
            query_hash=hashlib.sha256(result.clean_query.encode()).hexdigest(),
            latency_ms=result.latency_ms,
            cache_hit=result.cache_hit,
            chunk_count=len(result.chunks),
        )
    )

    return QueryResponse(
        answer=result.answer,
        session_id=result.session_id,
        cache_hit=result.cache_hit,
        latency_ms=result.latency_ms,
        chunk_count=len(result.chunks),
        pii_found=result.pii_found,
        pii_types=result.pii_types,
        llm_provider=result.provider,
        source_chunks=source_chunks,
        tokens_saved_pct=result.tokens_saved_pct,
    )
