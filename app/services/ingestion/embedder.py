"""Embedder using fastembed (local ONNX — no API key required).

Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 — 384-dim,
multilingual (entiende español), downloaded on first use.
"""
from __future__ import annotations

import asyncio
from functools import lru_cache

from fastembed import TextEmbedding

from app.core.constants import EMBEDDING_MODEL_LOCAL
from app.services.ingestion.chunker import Chunk


@lru_cache(maxsize=1)
def _get_model() -> TextEmbedding:
    return TextEmbedding(model_name=EMBEDDING_MODEL_LOCAL)


def _embed_sync(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    return [e.tolist() for e in model.embed(texts)]


async def _embed_texts(texts: list[str]) -> list[list[float]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed_sync, texts)


async def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    """Embed a list of chunks. Returns list of 384-dim vectors."""
    return await _embed_texts([c.text for c in chunks])


async def embed_query(text: str) -> list[float]:
    results = await _embed_texts([text])
    return results[0]
