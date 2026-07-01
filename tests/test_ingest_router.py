"""Tests for the /ingest endpoint — verifies PII scrubbing at ingest time."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.document import Document  # noqa: F401 — registers table in Base.metadata


@pytest.fixture
async def db_session(tmp_path):
    # Use a file-based SQLite db so all pool connections share the same tables.
    # In-memory SQLite (:memory:) creates a separate database per connection,
    # which breaks when the session opens a new connection after DDL.
    db_file = str(tmp_path / "test.db")
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def app_client(db_session: AsyncSession):
    from fastapi import FastAPI

    from app.api.routers import ingest
    from app.models.database import get_db

    test_app = FastAPI()
    test_app.include_router(ingest.router)

    async def override_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sample_txt() -> bytes:
    return b"El empleado tiene 15 dias de vacaciones al anio."


@pytest.fixture
def pii_txt() -> bytes:
    return (
        b"El empleado 12.345.678-9 con correo ana@empresa.cl "
        b"debe presentar el formulario antes del plazo."
    )


async def test_ingest_clean_document(app_client: AsyncClient, sample_txt: bytes) -> None:
    """A document without PII ingests normally with pii_scrubbed=False."""
    with (
        patch(
            "app.api.routers.ingest.embed_chunks",
            new_callable=AsyncMock,
            return_value=[[0.1] * 1536],
        ),
        patch("app.api.routers.ingest.upsert_chunks", new_callable=AsyncMock),
    ):
        resp = await app_client.post(
            "/ingest",
            files={"file": ("policy.txt", sample_txt, "text/plain")},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["pii_scrubbed"] is False


async def test_ingest_pii_document_sets_flag(
    app_client: AsyncClient, pii_txt: bytes
) -> None:
    """A document containing PII is scrubbed before chunking; response flags it."""
    captured_chunks: list = []

    async def mock_embed(chunks):  # type: ignore[no-untyped-def]
        captured_chunks.extend(chunks)
        return [[0.1] * 1536] * len(chunks)

    with (
        patch("app.api.routers.ingest.embed_chunks", side_effect=mock_embed),
        patch("app.api.routers.ingest.upsert_chunks", new_callable=AsyncMock),
    ):
        resp = await app_client.post(
            "/ingest",
            files={"file": ("hr.txt", pii_txt, "text/plain")},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["pii_scrubbed"] is True

    # Raw PII must not appear in the text that was passed to the embedder
    all_text = " ".join(c.text for c in captured_chunks)
    assert "12.345.678-9" not in all_text
    assert "ana@empresa.cl" not in all_text


async def test_ingest_unreadable_file_returns_clear_error(
    app_client: AsyncClient,
) -> None:
    """A file with no readable text (e.g. an image/scan) must fail with a clear
    422 message, not silently index zero chunks nor a generic 500."""
    with (
        patch("app.api.routers.ingest.embed_chunks", new_callable=AsyncMock),
        patch("app.api.routers.ingest.upsert_chunks", new_callable=AsyncMock),
    ):
        resp = await app_client.post(
            "/ingest",
            files={"file": ("escaneo.txt", b"   \n  \n ", "text/plain")},
        )

    assert resp.status_code == 422
    assert "texto legible" in resp.json()["detail"]


async def test_ingest_unsupported_type_message_in_spanish(
    app_client: AsyncClient,
) -> None:
    """An unsupported type is rejected with a helpful Spanish message."""
    resp = await app_client.post(
        "/ingest",
        files={"file": ("foto.png", b"\x89PNG\r\n", "image/png")},
    )
    assert resp.status_code == 400
    assert "no soportado" in resp.json()["detail"]
