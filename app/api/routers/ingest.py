import hashlib
import time
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.ingest import IngestResponse
from app.core.auth import require_api_key
from app.core.config import settings
from app.core.logging import get_logger
from app.core.rate_limit import rate_limit
from app.models.database import get_db
from app.models.document import Document
from app.services.ingestion.chunker import semantic_chunk
from app.services.ingestion.embedder import embed_chunks
from app.services.ingestion.extractor import extract_text
from app.services.privacy.scrubber import PIIScrubber
from app.services.vector_store import upsert_chunks

logger = get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post(
    "",
    response_model=IngestResponse,
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
async def ingest_document(
    file: UploadFile,
    session_id: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    # Each upload is owned by a session so search can isolate it from other
    # users and cleanup can expire it. No session given -> orphan (still purged).
    owner_session = session_id or str(uuid.uuid4())
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB.",
        )
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

    pii_scrubbed = False
    try:
        text = extract_text(content, filename)

        # Scrub PII from document text before chunking/embedding
        # so the vector store never holds raw identifiers
        scrubber = PIIScrubber(spacy_enabled=settings.spacy_enabled)
        clean_text, _token_map, pii_types = scrubber.scrub(text)
        if _token_map:
            pii_scrubbed = True
            logger.info(
                "ingest_pii_scrubbed",
                filename=filename,
                doc_id=doc_id,
                pii_types=pii_types,
            )

        chunks = semantic_chunk(clean_text, doc_id=doc_id)
        embeddings = await embed_chunks(chunks)
        await upsert_chunks(
            doc_id,
            chunks,
            embeddings,
            metadata_extra={
                "source": "upload",
                "session_id": owner_session,
                "uploaded_at": time.time(),
            },
        )

        doc.chunk_count = len(chunks)
        doc.status = "ready"
        await db.commit()

        logger.info(
            "ingest_complete",
            filename=filename,
            doc_id=doc.id,
            chunks=len(chunks),
            pii_scrubbed=pii_scrubbed,
        )

        # Fire Telegram notification async (non-blocking)
        import asyncio  # noqa: PLC0415

        from app.services.telegram_service import notify_ingest  # noqa: PLC0415

        asyncio.create_task(notify_ingest(filename, len(chunks)))

    except Exception as exc:
        doc.status = "error"
        await db.commit()
        # Log the detail server-side; return a generic message (no internals to the user).
        logger.error("ingest_failed", filename=filename, error=str(exc))
        raise HTTPException(
            status_code=500, detail="No se pudo procesar el archivo. Inténtalo de nuevo."
        ) from exc

    return IngestResponse(
        doc_id=doc.id,
        filename=filename,
        chunk_count=len(chunks),
        status="ready",
        pii_scrubbed=pii_scrubbed,
    )
