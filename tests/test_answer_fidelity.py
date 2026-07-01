"""Tests del guardarraíl de fidelidad al documento (spec 006, P1).

Verifican que, cuando el mejor chunk recuperado no alcanza el umbral de respuesta,
el sistema se niega SIN llamar al LLM; y que el prompt del sistema instruye la
negativa para conocimiento general.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.core.config as config_module
from app.core.constants import NO_INFO_MESSAGE, SYSTEM_PROMPT
from app.models.base import Base
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


def test_system_prompt_forbids_general_knowledge() -> None:
    # El prompt debe prohibir explícitamente responder con conocimiento general
    # (matemáticas, historia) y fijar la frase canónica de negativa.
    assert NO_INFO_MESSAGE in SYSTEM_PROMPT
    lowered = SYSTEM_PROMPT.lower()
    assert "matemátic" in lowered
    assert "históric" in lowered


async def test_low_similarity_refuses_without_llm(
    db_session: AsyncSession, monkeypatch
) -> None:
    """Con la perilla activada, un chunk por debajo del umbral → negativa sin LLM."""
    monkeypatch.setattr(config_module.settings, "answer_min_similarity", 0.80)

    llm_called = False

    async def mock_complete(system: str, user: str) -> str:
        nonlocal llm_called
        llm_called = True
        return "no debería llamarse"

    mock_llm = MagicMock()
    mock_llm.complete = mock_complete
    mock_llm.provider_name = "mock"

    # distance 0.4 → similarity 0.6, por debajo del umbral 0.80.
    weak_chunk = SearchResult(chunk_id="d_0", text="algo", doc_id="d", distance=0.4)

    with (
        patch("app.services.rag_pipeline.embed_query", new_callable=AsyncMock) as mock_embed,
        patch("app.services.rag_pipeline.search", new_callable=AsyncMock) as mock_search,
        patch("app.services.rag_pipeline._get_llm", return_value=mock_llm),
    ):
        mock_embed.return_value = [0.1] * 8
        mock_search.return_value = [weak_chunk]

        pipeline = RAGPipeline(db_session)
        result = await pipeline.query(
            "00000000-0000-0000-0000-000000000009", "¿cuánto es 2+2?"
        )

    assert llm_called is False
    assert "No encontré" in result.answer


async def test_strong_similarity_still_answers(
    db_session: AsyncSession, monkeypatch
) -> None:
    """Un chunk por encima del umbral sí llega al LLM (no hay falso rechazo)."""
    monkeypatch.setattr(config_module.settings, "answer_min_similarity", 0.55)

    async def mock_complete(system: str, user: str) -> str:
        return "La renta mensual es de $650.000."

    mock_llm = MagicMock()
    mock_llm.complete = mock_complete
    mock_llm.provider_name = "mock"

    strong_chunk = SearchResult(
        chunk_id="d_0", text="Renta mensual: $650.000.", doc_id="d", distance=0.2
    )  # similarity 0.8 > 0.55

    with (
        patch("app.services.rag_pipeline.embed_query", new_callable=AsyncMock) as mock_embed,
        patch("app.services.rag_pipeline.search", new_callable=AsyncMock) as mock_search,
        patch("app.services.rag_pipeline._get_llm", return_value=mock_llm),
    ):
        mock_embed.return_value = [0.1] * 8
        mock_search.return_value = [strong_chunk]

        pipeline = RAGPipeline(db_session)
        result = await pipeline.query(
            "00000000-0000-0000-0000-000000000010", "¿cuál es la renta?"
        )

    assert "650.000" in result.answer
