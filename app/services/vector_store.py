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


async def upsert_chunks(doc_id: str, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    """Insert or update chunks in the vector store."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _sync_upsert, doc_id, chunks, embeddings)


def _sync_upsert(doc_id: str, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    col = _get_collection()
    ids = [f"{doc_id}_{c.index}" for c in chunks]
    documents = [c.text for c in chunks]
    metadatas = [{"doc_id": doc_id, "index": c.index} for c in chunks]
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
) -> list[SearchResult]:
    """Search for similar chunks. Filter by cosine distance (1 - similarity)."""
    if threshold is None:
        threshold = settings.cosine_similarity_threshold
    distance_threshold = 1.0 - threshold

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        _executor, _sync_search, query_embedding, n_results
    )

    filtered = [r for r in results if r.distance <= distance_threshold]
    logger.info(
        "vectorstore_search",
        total=len(results),
        passed_threshold=len(filtered),
        threshold=threshold,
    )
    return filtered


def _sync_search(query_embedding: list[float], n_results: int) -> list[SearchResult]:
    col = _get_collection()
    count = col.count()
    if count == 0:
        return []

    actual_n = min(n_results, count)
    raw = col.query(
        query_embeddings=[query_embedding],
        n_results=actual_n,
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
