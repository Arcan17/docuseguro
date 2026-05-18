import hashlib

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.ingest import IngestResponse
from app.core.logging import get_logger
from app.models.database import get_db
from app.models.document import Document
from app.services.ingestion.chunker import semantic_chunk
from app.services.ingestion.embedder import embed_chunks
from app.services.ingestion.extractor import extract_text
from app.services.vector_store import upsert_chunks

logger = get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()

    # Dedup: skip re-ingestion of identical content
    existing = await db.scalar(select(Document).where(Document.content_hash == content_hash))
    if existing:
        logger.info("ingest_skipped_duplicate", filename=filename, doc_id=existing.id)
        return IngestResponse(
            doc_id=existing.id,
            filename=existing.filename,
            chunk_count=existing.chunk_count,
            status="duplicate",
        )

    doc = Document(
        filename=filename,
        content_hash=content_hash,
        file_size=len(content),
        status="processing",
    )
    db.add(doc)
    await db.flush()  # get id without committing
    doc_id = str(doc.id)

    try:
        text = extract_text(content, filename)
        chunks = semantic_chunk(text, doc_id=doc_id)
        embeddings = await embed_chunks(chunks)
        await upsert_chunks(doc_id, chunks, embeddings)

        doc.chunk_count = len(chunks)
        doc.status = "ready"
        await db.commit()

        logger.info("ingest_complete", filename=filename, doc_id=doc.id, chunks=len(chunks))

        # Fire Telegram notification async (non-blocking)
        import asyncio  # noqa: PLC0415

        from app.services.telegram_service import notify_ingest  # noqa: PLC0415

        asyncio.create_task(notify_ingest(filename, len(chunks)))

    except Exception as exc:
        doc.status = "error"
        await db.commit()
        logger.error("ingest_failed", filename=filename, error=str(exc))
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return IngestResponse(
        doc_id=doc.id,
        filename=filename,
        chunk_count=len(chunks),
        status="ready",
    )
