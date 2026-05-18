from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.query import QueryRequest, QueryResponse, SourceChunk
from app.models.database import get_db
from app.services.rag_pipeline import RAGPipeline

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    pipeline = RAGPipeline(db)
    result = await pipeline.query(
        session_id=request.session_id,
        query_text=request.query,
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
        notify_query(request.query, result.answer, result.latency_ms, result.cache_hit)
    )
    asyncio.create_task(
        log_crm_event(
            query_hash=result.chunks[0].chunk_id if result.chunks else "none",
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
