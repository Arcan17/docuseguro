from openai import AsyncOpenAI

from app.core.config import settings
from app.core.constants import EMBEDDING_BATCH_SIZE, EMBEDDING_MODEL
from app.services.ingestion.chunker import Chunk

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    """Embed a list of chunks in batches. Returns list of embedding vectors."""
    texts = [c.text for c in chunks]
    return await _embed_texts(texts)


async def embed_query(text: str) -> list[float]:
    results = await _embed_texts([text])
    return results[0]


async def _embed_texts(texts: list[str]) -> list[list[float]]:
    client = _get_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i : i + EMBEDDING_BATCH_SIZE]
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )
        all_embeddings.extend([item.embedding for item in response.data])

    return all_embeddings
