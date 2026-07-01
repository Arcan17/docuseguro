"""Tests de la restauración de PII del DOCUMENTO en las respuestas (spec 006, P1b)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.services.privacy.doc_pii import (
    build_presentation,
    load_doc_maps,
    persist_doc_map,
)
from app.services.rag_pipeline import RAGPipeline
from app.services.vector_store import SearchResult


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def test_build_presentation_no_collision_between_docs() -> None:
    # Dos documentos, cada uno con su [RUT_1] apuntando a personas distintas.
    doc_maps = {
        "docA": {"RUT_1": "11.111.111-1"},
        "docB": {"RUT_1": "22.222.222-2"},
    }
    chunks = [("Cliente [RUT_1] de A", "docA"), ("Cliente [RUT_1] de B", "docB")]
    pres = build_presentation(chunks, doc_maps, "consulta sin pii", {})

    # Cada RUT real recibe un marcador de presentación distinto → sin colisión.
    joined = " ".join(pres.chunk_texts)
    assert "[RUT_1]" in joined and "[RUT_2]" in joined
    assert set(pres.display_map.values()) == {"11.111.111-1", "22.222.222-2"}


def test_build_presentation_dedupes_same_value() -> None:
    # El mismo valor en documento y consulta comparte marcador.
    doc_maps = {"d": {"RUT_1": "12.345.678-9"}}
    chunks = [("El arrendatario [RUT_1]", "d")]
    query_map = {"RUT_1": "12.345.678-9"}
    pres = build_presentation(chunks, doc_maps, "¿el RUT [RUT_1] tiene deudas?", query_map)

    assert len(pres.display_map) == 1
    assert list(pres.display_map.values()) == ["12.345.678-9"]


async def test_persist_and_load_doc_map(db_session: AsyncSession) -> None:
    await persist_doc_map(
        db_session, "doc-9", {"RUT_1": "12.345.678-9", "CORREO_1": "a@b.cl"}, None
    )
    maps = await load_doc_maps(db_session, {"doc-9"})
    assert maps["doc-9"]["RUT_1"] == "12.345.678-9"
    assert maps["doc-9"]["CORREO_1"] == "a@b.cl"


async def test_document_pii_restored_with_real_value(db_session: AsyncSession) -> None:
    """El RUT del documento vuelve legible y con su valor real en la respuesta,
    y el texto enviado a la IA NO contiene el valor real."""
    await persist_doc_map(db_session, "doc-1", {"RUT_1": "12.345.678-9"}, None)

    captured_prompts: list[str] = []

    async def mock_complete(system: str, user: str) -> str:
        captured_prompts.append(user)
        return "El RUT del arrendatario es [RUT_1]."

    mock_llm = MagicMock()
    mock_llm.complete = mock_complete
    mock_llm.provider_name = "mock"

    # Chunk almacenado con el marcador del documento (el valor real vive en la DB).
    chunk = SearchResult(
        chunk_id="doc-1_0", text="Arrendatario: [RUT_1].", doc_id="doc-1", distance=0.1
    )

    with (
        patch("app.services.rag_pipeline.embed_query", new_callable=AsyncMock) as mock_embed,
        patch("app.services.rag_pipeline.search", new_callable=AsyncMock) as mock_search,
        patch("app.services.rag_pipeline._get_llm", return_value=mock_llm),
    ):
        mock_embed.return_value = [0.1] * 8
        mock_search.return_value = [chunk]

        pipeline = RAGPipeline(db_session)
        result = await pipeline.query(
            "00000000-0000-0000-0000-000000000021", "¿cuál es el RUT del arrendatario?"
        )

    # La respuesta muestra el valor real y legible.
    assert "12.345.678-9" in result.answer
    assert "[RUT_1]" not in result.answer
    # La IA nunca vio el valor real.
    assert captured_prompts and "12.345.678-9" not in captured_prompts[0]
