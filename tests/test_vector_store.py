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

    _sync_upsert("doc_1", chunks, embeddings, {"source": "upload", "session_id": "s1"})

    # The owning session sees its own upload
    results = _sync_search(_make_embedding(0.9), n_results=2, session_id="s1")
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)


def test_uploads_are_isolated_per_session(temp_chroma) -> None:
    chunks = [Chunk(text="Documento confidencial del usuario A.", index=0, doc_id="docA")]
    _sync_upsert("docA", chunks, [_make_embedding(0.9)], {"source": "upload", "session_id": "userA"})

    # A different session must NOT retrieve user A's upload
    results = _sync_search(_make_embedding(0.9), n_results=5, session_id="userB")
    assert results == []


def test_demo_docs_visible_to_any_session(temp_chroma) -> None:
    chunks = [Chunk(text="Documento de ejemplo compartido.", index=0, doc_id="demo1")]
    _sync_upsert("demo1", chunks, [_make_embedding(0.9)], {"source": "demo"})

    results = _sync_search(_make_embedding(0.9), n_results=5, session_id="cualquiera")
    assert len(results) > 0


def test_search_empty_store(temp_chroma) -> None:
    results = _sync_search(_make_embedding(0.5), n_results=5)
    assert results == []


def test_similarity_property() -> None:
    r = SearchResult(chunk_id="id", text="t", doc_id="d", distance=0.2)
    assert abs(r.similarity - 0.8) < 1e-9
