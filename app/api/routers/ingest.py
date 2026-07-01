import hashlib
import time
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.api.schemas.ingest import IngestResponse
from app.core.auth import require_api_key
from app.core.config import settings
from app.core.logging import get_logger
from app.core.rate_limit import rate_limit
from app.core.trial import ensure_trial_active
from app.models.database import get_db
from app.models.document import Document
from app.models.user import User
from app.services.ingestion.chunker import semantic_chunk
from app.services.ingestion.embedder import embed_chunks
from app.services.ingestion.extractor import extract_text
from app.services.privacy.doc_pii import persist_doc_map
from app.services.privacy.scrubber import PIIScrubber
from app.services.vector_store import upsert_chunks

logger = get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".xlsx", ".pptx", ".csv"}


@router.post(
    "",
    response_model=IngestResponse,
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
async def ingest_document(
    file: UploadFile,
    session_id: str = Form(default=""),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    # Authenticated users with an expired trial cannot upload (anonymous users pass).
    ensure_trial_active(user)
    # Owner = the account (persistent) if authenticated, else the browser session
    # (anonymous, ephemeral). Search isolates by this owner; cleanup only expires
    # anonymous uploads.
    if user is not None:
        owner = f"user:{user.id}"
        source = "user"
        doc_user_id: int | None = user.id
    else:
        owner = session_id or str(uuid.uuid4())
        source = "upload"
        doc_user_id = None
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        permitidos = ", ".join(sorted(e.lstrip(".") for e in ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tipo de archivo no soportado ({ext or 'sin extensión'}). "
                f"Por ahora aceptamos: {permitidos}. "
                "Si es una imagen o un PDF escaneado, todavía no podemos leerlo."
            ),
        )

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB.",
        )
    content_hash = hashlib.sha256(content).hexdigest()

    # Dedup only for authenticated users: their docs persist across sessions so
    # skipping re-indexing is safe. Anonymous sessions are ephemeral — the same
    # file may be uploaded in a new session with a fresh ChromaDB owner bucket,
    # so we always re-index to avoid returning a stale doc whose vectors live
    # under a different session_id.
    if doc_user_id is not None:
        existing = await db.scalar(
            select(Document).where(
                Document.content_hash == content_hash,
                Document.user_id == doc_user_id,
            )
        )
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
        user_id=doc_user_id,
    )
    db.add(doc)
    await db.flush()  # get id without committing
    doc_id = str(doc.id)

    pii_scrubbed = False

    # Extract text in isolation first. A file we cannot parse (corrupt, password
    # protected, or an image/scan with no text layer) is a problem with the file,
    # not the server — surface a clear message instead of a generic 500 or a
    # silent zero-chunk "success".
    try:
        text = extract_text(content, filename)
    except Exception as exc:
        doc.status = "error"
        await db.commit()
        logger.warning("ingest_extract_failed", filename=filename, error=str(exc))
        raise HTTPException(
            status_code=422,
            detail=(
                "No pudimos leer el contenido de este archivo. Puede estar dañado, "
                "protegido con contraseña, o ser una imagen/escaneo sin texto "
                "seleccionable."
            ),
        ) from exc

    if len(text.strip()) < 20:
        doc.status = "error"
        await db.commit()
        logger.info("ingest_no_text", filename=filename, chars=len(text.strip()))
        raise HTTPException(
            status_code=422,
            detail=(
                "No encontramos texto legible en el archivo. Si es una foto o un PDF "
                "escaneado, todavía no podemos leerlo (la lectura de imágenes está en "
                "camino)."
            ),
        )

    try:
        # Scrub PII from document text before chunking/embedding
        # so the vector store never holds raw identifiers
        scrubber = PIIScrubber(spacy_enabled=settings.spacy_enabled)
        clean_text, doc_token_map, pii_types = scrubber.scrub(text)
        if doc_token_map:
            pii_scrubbed = True
            logger.info(
                "ingest_pii_scrubbed",
                filename=filename,
                doc_id=doc_id,
                pii_types=pii_types,
            )

        chunks = semantic_chunk(clean_text, doc_id=doc_id)
        embeddings = await embed_chunks(chunks)
        meta: dict[str, object] = {"source": source, "session_id": owner}
        if source == "upload":
            # Only anonymous uploads carry a timestamp and are auto-expired.
            meta["uploaded_at"] = time.time()
        await upsert_chunks(doc_id, chunks, embeddings, metadata_extra=meta)

        # Keep the document's PII map so its identifiers can be restored (with their
        # real values) in answers. Stored in the relational DB, never in the vector
        # store. Anonymous uploads expire with their chunks; account docs persist.
        doc_pii_expires = (
            datetime.now(UTC) + timedelta(seconds=settings.upload_ttl_seconds)
            if doc_user_id is None
            else None
        )
        await persist_doc_map(db, doc_id, doc_token_map, doc_pii_expires)

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
