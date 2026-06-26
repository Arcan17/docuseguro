"""Test: sin cuenta, el modo anónimo sigue siendo efímero (source=upload, sin user_id)."""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.document import Document
from app.models.user import User  # noqa: F401 — register table


@pytest.fixture
async def db_session(tmp_path):
    db_file = str(tmp_path / "anon.db")
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession):
    from fastapi import FastAPI

    from app.api.routers import ingest
    from app.models.database import get_db

    app = FastAPI()
    app.include_router(ingest.router)

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_anonymous_upload_is_ephemeral(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    captured: dict = {}

    async def fake_upsert(doc_id, chunks, embeddings, metadata_extra=None):
        captured.update(metadata_extra or {})

    with (
        patch("app.api.routers.ingest.embed_chunks", new_callable=AsyncMock, return_value=[[0.1] * 8]),
        patch("app.api.routers.ingest.upsert_chunks", side_effect=fake_upsert),
    ):
        resp = await client.post(
            "/ingest",
            files={"file": ("demo.txt", b"Documento anonimo de prueba.", "text/plain")},
            data={"session_id": "00000000-0000-0000-0000-000000000abc"},
        )

    assert resp.status_code == 200
    # Sigue siendo anónimo y efímero, como antes.
    assert captured["source"] == "upload"
    assert "uploaded_at" in captured  # los anónimos se auto-eliminan por TTL

    doc = await db_session.scalar(select(Document))
    assert doc is not None and doc.user_id is None
