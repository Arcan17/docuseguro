import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb import Collection

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ingestion.chunker import Chunk

logger = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)
_client: Any = None  # chromadb.api.client.Client
_collection: Collection | None = None


def _get_collection() -> Collection:
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.chroma_path)
        _collection = _client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    doc_id: str
    distance: float

    @property
    def similarity(self) -> float:
        return 1.0 - self.distance


async def upsert_chunks(
    doc_id: str,
    chunks: list[Chunk],
    embeddings: list[list[float]],
    metadata_extra: dict[str, Any] | None = None,
) -> None:
    """Insert or update chunks in the vector store.

    `metadata_extra` is merged into every chunk's metadata — used to tag the
    owning session and source ("demo" vs "upload") so search can isolate a
    user's uploads from everyone else's and cleanup can expire them.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        _executor, _sync_upsert, doc_id, chunks, embeddings, metadata_extra
    )


def _sync_upsert(
    doc_id: str,
    chunks: list[Chunk],
    embeddings: list[list[float]],
    metadata_extra: dict[str, Any] | None = None,
) -> None:
    col = _get_collection()
    ids = [f"{doc_id}_{c.index}" for c in chunks]
    documents = [c.text for c in chunks]
    metadatas: list[dict[str, Any]] = []
    for c in chunks:
        meta: dict[str, Any] = {"doc_id": doc_id, "index": c.index}
        if metadata_extra:
            meta.update(metadata_extra)
        metadatas.append(meta)
    col.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    logger.info("vectorstore_upsert", doc_id=doc_id, count=len(chunks))


async def vector_count() -> int:
    """Number of chunks currently in the vector store.

    Gates demo seeding: the vector store lives on the container filesystem
    (ephemeral on Railway) while PostgreSQL is persistent, so they can drift
    out of sync after a redeploy. Seeding must key off this count, not the
    Document table, or the demo ends up with rows but no searchable vectors.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: _get_collection().count())


async def search(
    query_embedding: list[float],
    n_results: int = 5,
    threshold: float | None = None,
    session_id: str | None = None,
) -> list[SearchResult]:
    """Search for similar chunks. Filter by cosine distance (1 - similarity).

    Isolation: a query only retrieves the shared demo documents plus the
    chunks uploaded by `session_id`. One user can never see another user's
    uploaded documents.
    """
    if threshold is None:
        threshold = settings.cosine_similarity_threshold
    distance_threshold = 1.0 - threshold

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        _executor, _sync_search, query_embedding, n_results, session_id
    )

    filtered = [r for r in results if r.distance <= distance_threshold]
    logger.info(
        "vectorstore_search",
        total=len(results),
        passed_threshold=len(filtered),
        threshold=threshold,
    )
    return filtered


def _sync_search(
    query_embedding: list[float], n_results: int, session_id: str | None = None
) -> list[SearchResult]:
    col = _get_collection()
    count = col.count()
    if count == 0:
        return []

    # Isolation strategy: if the session has uploaded its own documents, search
    # *only* those — don't mix with demo docs. Mixing causes Spanish demo chunks
    # to outscore English user uploads for Spanish queries (bge-small-en-v1.5 is
    # English-focused; the demo docs are in Spanish and pull ahead on cosine sim).
    # Fall back to demo-only when the session has no chunks of its own.
    where: dict[str, Any] | None
    if session_id:
        try:
            probe = col.get(where={"session_id": session_id}, limit=1)
            has_session = bool(probe.get("ids"))
        except Exception:
            has_session = False
        where = {"session_id": session_id} if has_session else {"source": "demo"}
    else:
        where = {"source": "demo"}

    actual_n = min(n_results, count)
    raw = col.query(
        query_embeddings=[query_embedding],
        n_results=actual_n,
        where=where,
        include=["documents", "distances", "metadatas"],
    )

    results: list[SearchResult] = []
    for chunk_id, text, distance, meta in zip(
        raw["ids"][0],
        raw["documents"][0],  # type: ignore[index]
        raw["distances"][0],  # type: ignore[index]
        raw["metadatas"][0],  # type: ignore[index]
    ):
        results.append(
            SearchResult(
                chunk_id=chunk_id,
                text=text,
                doc_id=str(meta.get("doc_id", "")),
                distance=float(distance),
            )
        )
    return results


async def delete_document(doc_id: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _sync_delete, doc_id)


def _sync_delete(doc_id: str) -> None:
    col = _get_collection()
    col.delete(where={"doc_id": doc_id})


async def delete_by_owner(owner: str) -> None:
    """Delete every chunk owned by `owner` (e.g. 'user:42'). Used on account deletion."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _sync_delete_by_owner, owner)


def _sync_delete_by_owner(owner: str) -> None:
    col = _get_collection()
    col.delete(where={"session_id": owner})


async def delete_expired_uploads(ttl_seconds: int) -> None:
    """Delete user-uploaded chunks older than `ttl_seconds`.

    Demo docs (source="demo") are never deleted. This is what makes the
    "what you upload is not stored" promise true: uploads are purged on a
    timer so a user's document does not linger in the vector store.
    """
    import time  # noqa: PLC0415

    cutoff = time.time() - ttl_seconds
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _sync_delete_expired_uploads, cutoff)


def _sync_delete_expired_uploads(cutoff: float) -> None:
    col = _get_collection()
    col.delete(
        where={"$and": [{"source": "upload"}, {"uploaded_at": {"$lt": cutoff}}]}
    )
