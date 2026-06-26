"""Tests: aislamiento por cuenta y que un upload autenticado persiste (source=user)."""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.document import Document
from app.models.user import User  # noqa: F401 — register table
from app.services.ingestion.chunker import Chunk
from app.services.vector_store import _sync_search, _sync_upsert


def _emb(seed: float, dim: int = 8) -> list[float]:
    return [seed * (i + 1) / dim for i in range(dim)]


@pytest.fixture
def temp_chroma(tmp_path):
    with patch("app.services.vector_store.settings") as s:
        s.chroma_path = str(tmp_path / "chroma")
        s.chroma_collection = "iso_test"
        s.cosine_similarity_threshold = 0.5
        import app.services.vector_store as vs

        vs._client = None
        vs._collection = None
        yield
        vs._client = None
        vs._collection = None


def test_two_accounts_are_isolated(temp_chroma) -> None:
    # Doc de la cuenta A (owner = user:1) y doc demo compartido.
    _sync_upsert("a", [Chunk(text="Contrato de la empresa A.", index=0, doc_id="a")], [_emb(0.9)], {"source": "user", "session_id": "user:1"})
    _sync_upsert("demo1", [Chunk(text="Documento de ejemplo.", index=0, doc_id="demo1")], [_emb(0.9)], {"source": "demo"})

    # Usuario B (owner = user:2) NO ve el doc de A...
    b_results = _sync_search(_emb(0.9), n_results=5, session_id="user:2")
    assert all(r.doc_id != "a" for r in b_results)
    # ...pero A sí ve el suyo, y B ve el demo.
    a_results = _sync_search(_emb(0.9), n_results=5, session_id="user:1")
    assert any(r.doc_id == "a" for r in a_results)
    assert any(r.doc_id == "demo1" for r in b_results)


@pytest.fixture
async def db_session(tmp_path):
    db_file = str(tmp_path / "acc.db")
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

    from app.api.routers import auth, ingest
    from app.models.database import get_db

    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(ingest.router)

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_authenticated_upload_is_owned_and_persistent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    reg = await client.post("/auth/register", json={"email": "owner@b.cl", "password": "secret12"})
    token = reg.json()["access_token"]

    captured: dict = {}

    async def fake_upsert(doc_id, chunks, embeddings, metadata_extra=None):
        captured.update(metadata_extra or {})

    with (
        patch("app.api.routers.ingest.embed_chunks", new_callable=AsyncMock, return_value=[[0.1] * 8]),
        patch("app.api.routers.ingest.upsert_chunks", side_effect=fake_upsert),
    ):
        resp = await client.post(
            "/ingest",
            files={"file": ("mio.txt", b"Mi documento privado de prueba.", "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    # Etiquetado como de cuenta (persistente), no como anónimo efímero.
    assert captured["source"] == "user"
    assert captured["session_id"].startswith("user:")
    assert "uploaded_at" not in captured  # los de cuenta no expiran

    doc = await db_session.scalar(select(Document))
    assert doc is not None and doc.user_id is not None
