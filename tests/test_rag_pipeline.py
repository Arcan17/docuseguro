from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


def _make_chunk(text: str = "Política de vacaciones: 15 días hábiles.") -> SearchResult:
    return SearchResult(chunk_id="doc_1_0", text=text, doc_id="doc_1", distance=0.1)


async def test_query_strips_pii_before_llm(db_session: AsyncSession) -> None:
    """PII in the query must be replaced before reaching the LLM."""
    captured_prompts: list[str] = []

    async def mock_complete(system: str, user: str) -> str:
        captured_prompts.append(user)
        return "El empleado cumplió con los requisitos."

    mock_llm = MagicMock()
    mock_llm.complete = mock_complete
    mock_llm.provider_name = "mock"

    with (
        patch("app.services.rag_pipeline.embed_query", new_callable=AsyncMock) as mock_embed,
        patch("app.services.rag_pipeline.search", new_callable=AsyncMock) as mock_search,
        patch("app.services.rag_pipeline._get_llm", return_value=mock_llm),
    ):
        mock_embed.return_value = [0.1] * 8
        mock_search.return_value = [_make_chunk()]

        pipeline = RAGPipeline(db_session)
        result = await pipeline.query(
            session_id="00000000-0000-0000-0000-000000000001",
            query_text="¿Cumplió el empleado 12.345.678-9 con la política?",
        )

    assert len(captured_prompts) == 1
    # PII must NOT appear in what was sent to LLM
    assert "12.345.678-9" not in captured_prompts[0]
    assert result.pii_found is True
    assert "rut" in result.pii_types


async def test_query_cache_hit_skips_llm(db_session: AsyncSession) -> None:
    """Second identical query should return from cache without calling LLM."""
    llm_call_count = 0

    async def mock_complete(system: str, user: str) -> str:
        nonlocal llm_call_count
        llm_call_count += 1
        return "Respuesta de la política de vacaciones."

    mock_llm = MagicMock()
    mock_llm.complete = mock_complete
    mock_llm.provider_name = "mock"

    with (
        patch("app.services.rag_pipeline.embed_query", new_callable=AsyncMock) as mock_embed,
        patch("app.services.rag_pipeline.search", new_callable=AsyncMock) as mock_search,
        patch("app.services.rag_pipeline._get_llm", return_value=mock_llm),
    ):
        mock_embed.return_value = [0.5] * 8
        mock_search.return_value = [_make_chunk()]

        pipeline = RAGPipeline(db_session)
        r1 = await pipeline.query("00000000-0000-0000-0000-000000000002", "¿Cuántos días de vacaciones?")
        r2 = await pipeline.query("00000000-0000-0000-0000-000000000002", "¿Cuántos días de vacaciones?")

    assert llm_call_count == 1
    assert r1.cache_hit is False
    assert r2.cache_hit is True


async def test_query_no_context_returns_message(db_session: AsyncSession) -> None:
    """When no chunks pass threshold, return graceful message without LLM call."""
    llm_called = False

    async def mock_complete(system: str, user: str) -> str:
        nonlocal llm_called
        llm_called = True
        return "never"

    mock_llm = MagicMock()
    mock_llm.complete = mock_complete
    mock_llm.provider_name = "mock"

    with (
        patch("app.services.rag_pipeline.embed_query", new_callable=AsyncMock) as mock_embed,
        patch("app.services.rag_pipeline.search", new_callable=AsyncMock) as mock_search,
        patch("app.services.rag_pipeline._get_llm", return_value=mock_llm),
    ):
        mock_embed.return_value = [0.1] * 8
        mock_search.return_value = []  # threshold filtered everything

        pipeline = RAGPipeline(db_session)
        result = await pipeline.query("00000000-0000-0000-0000-000000000003", "pregunta irrelevante")

    assert llm_called is False
    assert "No encontré" in result.answer
