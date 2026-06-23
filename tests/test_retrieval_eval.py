"""Retrieval evaluation tests.

Three test groups:

  1. Threshold filtering  — synthetic unit vectors, validates the 0.75 cosine boundary.
  2. Retrieval quality    — real fastembed embeddings on a controlled HR-policy dataset.
  3. PII-safe storage     — confirms raw PII never reaches the vector store at ingest time.
"""
from __future__ import annotations

import math
from unittest.mock import patch

import pytest

from app.services.ingestion.chunker import Chunk
from app.services.ingestion.embedder import _embed_sync
from app.services.privacy.restorer import restore
from app.services.privacy.scrubber import PIIScrubber
from app.services.vector_store import SearchResult, _sync_search, _sync_upsert, search

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _unit_vec(cosine_sim: float, dim: int = 8) -> list[float]:
    """Unit vector in R^dim whose cosine similarity to e₁=[1,0,…,0] equals cosine_sim."""
    sin_val = math.sqrt(max(0.0, 1.0 - cosine_sim**2))
    v = [0.0] * dim
    v[0] = cosine_sim
    v[1] = sin_val
    return v


def _store(doc_id: str, text: str, emb: list[float]) -> None:
    _sync_upsert(
        doc_id, [Chunk(text=text, index=0, doc_id=doc_id)], [emb], {"source": "demo"}
    )


_QUERY_8D = [1.0] + [0.0] * 7


@pytest.fixture
def chroma8(tmp_path):
    """Temporary 8-dim ChromaDB — for fast synthetic-vector tests."""
    with patch("app.services.vector_store.settings") as s:
        s.chroma_path = str(tmp_path / "chroma")
        s.chroma_collection = "test_8d"
        s.cosine_similarity_threshold = 0.75
        import app.services.vector_store as vs

        vs._client = None
        vs._collection = None
        yield s
        vs._client = None
        vs._collection = None


# ---------------------------------------------------------------------------
# 1. Threshold filtering — synthetic 8-dim unit vectors
# ---------------------------------------------------------------------------


async def test_chunk_above_threshold_is_returned(chroma8) -> None:
    """similarity=0.85 (distance=0.15) must pass the 0.75 threshold."""
    _store("hi", "Vacaciones: 15 días hábiles.", _unit_vec(0.85))
    results = await search(_QUERY_8D, n_results=5, threshold=0.75)
    assert any(r.chunk_id == "hi_0" for r in results)


async def test_chunk_below_threshold_is_filtered(chroma8) -> None:
    """similarity=0.60 (distance=0.40) must be filtered out."""
    _store("lo", "Contenido irrelevante.", _unit_vec(0.60))
    results = await search(_QUERY_8D, n_results=5, threshold=0.75)
    assert not any(r.chunk_id == "lo_0" for r in results)


async def test_mixed_store_returns_only_relevant_chunk(chroma8) -> None:
    """One chunk above and one below threshold: only the relevant one is returned."""
    _store("good", "Documento relevante.", _unit_vec(0.85))
    _store("bad", "Documento irrelevante.", _unit_vec(0.60))
    results = await search(_QUERY_8D, n_results=5, threshold=0.75)
    ids = {r.chunk_id for r in results}
    assert "good_0" in ids
    assert "bad_0" not in ids


async def test_results_ordered_by_descending_similarity(chroma8) -> None:
    """Multiple results must be sorted highest similarity first."""
    _store("best", "Primer resultado.", _unit_vec(0.92))
    _store("good", "Segundo resultado.", _unit_vec(0.80))
    results = await search(_QUERY_8D, n_results=5, threshold=0.75)
    assert len(results) == 2
    assert results[0].similarity >= results[1].similarity


def test_similarity_property_equals_one_minus_distance() -> None:
    """SearchResult.similarity == 1.0 - distance (property contract)."""
    for dist in [0.0, 0.1, 0.25, 0.5, 1.0]:
        r = SearchResult(chunk_id="x", text="t", doc_id="d", distance=dist)
        assert abs(r.similarity - (1.0 - dist)) < 1e-9


# ---------------------------------------------------------------------------
# 2. Retrieval quality — real fastembed embeddings (BAAI/bge-small-en-v1.5)
#    Controlled HR-policy eval dataset: 3 documents, 3 paired queries.
# ---------------------------------------------------------------------------

_EVAL_CORPUS = [
    {
        "id": "vacaciones",
        "text": (
            "Política de vacaciones: Los empleados con contrato indefinido tienen "
            "15 días hábiles de vacaciones anuales."
        ),
        "query": "¿Cuántos días de vacaciones tienen los empleados?",
    },
    {
        "id": "salud",
        "text": (
            "Beneficios de salud: La empresa cubre el 80% del plan de salud "
            "para empleados y sus cargas directas."
        ),
        "query": "¿Qué porcentaje del seguro de salud cubre la empresa?",
    },
    {
        "id": "teletrabajo",
        "text": (
            "Teletrabajo y trabajo remoto: Los empleados pueden trabajar en modalidad "
            "remota desde casa hasta 3 días hábiles por semana."
        ),
        "query": "¿Cuántos días de trabajo remoto están permitidos por semana?",
    },
]

_UNRELATED_QUERY = "¿Cuál es el precio del barril de petróleo hoy?"


@pytest.fixture
def chroma384(tmp_path):
    """Temporary ChromaDB configured for 384-dim fastembed vectors."""
    with patch("app.services.vector_store.settings") as s:
        s.chroma_path = str(tmp_path / "chroma384")
        s.chroma_collection = "eval_384"
        s.cosine_similarity_threshold = 0.75
        import app.services.vector_store as vs

        vs._client = None
        vs._collection = None
        yield s
        vs._client = None
        vs._collection = None


@pytest.fixture
def corpus(chroma384):
    """Load _EVAL_CORPUS into ChromaDB using real fastembed embeddings."""
    texts = [item["text"] for item in _EVAL_CORPUS]
    embeddings = _embed_sync(texts)
    for item, emb in zip(_EVAL_CORPUS, embeddings):
        _sync_upsert(
            item["id"],
            [Chunk(text=item["text"], index=0, doc_id=item["id"])],
            [emb],
            {"source": "demo"},
        )
    return chroma384


@pytest.mark.parametrize("item", _EVAL_CORPUS, ids=[e["id"] for e in _EVAL_CORPUS])
async def test_relevant_query_retrieves_matching_chunk(corpus, item: dict) -> None:
    """Each query must retrieve its paired document within the top-3 results."""
    query_emb = _embed_sync([item["query"]])[0]
    results = await search(query_emb, n_results=3, threshold=0.75)
    retrieved = [r.chunk_id for r in results]
    assert f"{item['id']}_0" in retrieved, (
        f"Expected '{item['id']}_0' for query '{item['query']}'. Got: {retrieved}"
    )


async def test_precision_at_1_across_corpus(corpus) -> None:
    """Top-ranked result for every eval query must be its own document (Precision@1 = 1.0)."""
    for item in _EVAL_CORPUS:
        query_emb = _embed_sync([item["query"]])[0]
        results = await search(query_emb, n_results=3, threshold=0.75)
        assert results, f"No results above threshold for: {item['query']}"
        assert results[0].chunk_id == f"{item['id']}_0", (
            f"Precision@1 failed for '{item['id']}': "
            f"expected '{item['id']}_0', got '{results[0].chunk_id}'"
        )


async def test_unrelated_query_returns_no_results(corpus) -> None:
    """A query with no semantic overlap with the HR corpus must return zero chunks."""
    query_emb = _embed_sync([_UNRELATED_QUERY])[0]
    results = await search(query_emb, n_results=5, threshold=0.75)
    assert results == [], (
        f"Expected empty results for unrelated query, got: {[r.chunk_id for r in results]}"
    )


# ---------------------------------------------------------------------------
# 3. PII-safe storage — raw PII must never reach the vector store
# ---------------------------------------------------------------------------

_PII_CASES = [
    ("rut", "El empleado con RUT 12.345.678-9 solicitó vacaciones.", "12.345.678-9"),
    ("email", "Contacto RRHH: rrhh@empresa.cl para consultas.", "rrhh@empresa.cl"),
    ("phone", "Llame al +56 9 8765 4321 para soporte.", "+56 9 8765 4321"),
]


@pytest.fixture
def scrubber() -> PIIScrubber:
    return PIIScrubber(spacy_enabled=False)


@pytest.mark.parametrize("pii_type,text,raw_pii", _PII_CASES, ids=[c[0] for c in _PII_CASES])
def test_stored_chunk_does_not_contain_raw_pii(
    chroma8, scrubber: PIIScrubber, pii_type: str, text: str, raw_pii: str
) -> None:
    """Scrubbed text is what gets stored: raw PII must not appear in any retrieved chunk."""
    clean_text, _map, _ = scrubber.scrub(text)
    assert raw_pii not in clean_text  # pre-condition: scrubber removed the PII

    _store(f"pii_{pii_type}", clean_text, _unit_vec(0.90))

    stored = _sync_search(_QUERY_8D, n_results=5)
    for r in stored:
        assert raw_pii not in r.text, (
            f"Raw PII '{raw_pii}' found in stored chunk: {r.text!r}"
        )


def test_token_map_preserves_original_pii_values(scrubber: PIIScrubber) -> None:
    """Token map must hold one entry per unique PII value with the original preserved."""
    text = "RUT 12.345.678-9 email test@empresa.cl"
    _, token_map, detected = scrubber.scrub(text)
    assert len(token_map) == 2
    assert set(detected) == {"rut", "email"}
    assert "12.345.678-9" in token_map.values()
    assert "test@empresa.cl" in token_map.values()


def test_ingest_pii_is_not_restorable_without_token_map(scrubber: PIIScrubber) -> None:
    """At ingest, token_map is discarded — stored text cannot be de-anonymised."""
    text = "Contrato del empleado RUT 12.345.678-9."
    clean_text, _token_map, _ = scrubber.scrub(text)

    # ingest.py discards _token_map; simulate that here
    stored_text = clean_text
    # Without the original token_map, restore() is a no-op
    not_restored = restore(stored_text, {})
    assert "12.345.678-9" not in not_restored
