from unittest.mock import patch

import pytest

from app.services.ingestion.chunker import Chunk
from app.services.vector_store import SearchResult, _sync_search, _sync_upsert


def _make_embedding(seed: float, dim: int = 8) -> list[float]:
    return [seed * (i + 1) / dim for i in range(dim)]


@pytest.fixture
def temp_chroma(tmp_path):
    with patch("app.services.vector_store.settings") as mock_settings:
        mock_settings.chroma_path = str(tmp_path / "chroma")
        mock_settings.chroma_collection = "test_col"
        mock_settings.cosine_similarity_threshold = 0.75
        # Reset module-level singletons
        import app.services.vector_store as vs
        vs._client = None
        vs._collection = None
        yield mock_settings
        vs._client = None
        vs._collection = None


def test_upsert_and_search(temp_chroma) -> None:
    chunks = [
        Chunk(text="Política de vacaciones para empleados.", index=0, doc_id="doc_1"),
        Chunk(text="Beneficios de salud corporativos.", index=1, doc_id="doc_1"),
    ]
    embeddings = [_make_embedding(0.9), _make_embedding(0.1)]

    _sync_upsert("doc_1", chunks, embeddings)

    # Search with embedding similar to first chunk
    results = _sync_search(_make_embedding(0.9), n_results=2)
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)


def test_search_empty_store(temp_chroma) -> None:
    results = _sync_search(_make_embedding(0.5), n_results=5)
    assert results == []


def test_similarity_property() -> None:
    r = SearchResult(chunk_id="id", text="t", doc_id="d", distance=0.2)
    assert abs(r.similarity - 0.8) < 1e-9
