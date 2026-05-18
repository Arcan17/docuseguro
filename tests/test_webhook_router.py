import httpx
import pytest
import respx
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.query_log import QueryLog


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def app_client(db_session: AsyncSession):
    from fastapi import FastAPI

    from app.api.routers import webhook

    test_app = FastAPI()
    test_app.include_router(webhook.router)

    from app.models.database import get_db

    async def override_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_db

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


async def test_crm_webhook_returns_ok(app_client: AsyncClient) -> None:
    payload = {
        "query_hash": "abc123",
        "latency_ms": 350,
        "cache_hit": False,
        "chunk_count": 3,
        "source": "privrag",
    }
    response = await app_client.post("/webhook/crm", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "received_at" in data


async def test_crm_webhook_logs_to_db(app_client: AsyncClient, db_session: AsyncSession) -> None:
    payload = {
        "query_hash": "deadbeef",
        "latency_ms": 200,
        "cache_hit": True,
        "chunk_count": 2,
    }
    await app_client.post("/webhook/crm", json=payload)

    rows = (await db_session.execute(select(QueryLog))).scalars().all()
    assert len(rows) == 1
    assert rows[0].cache_hit is True
    assert rows[0].latency_ms == 200


@respx.mock
async def test_telegram_not_called_when_disabled() -> None:
    """When TELEGRAM_BOT_TOKEN is empty, no HTTP request to Telegram should fire."""
    from app.services.telegram_service import notify_query

    route = respx.post("https://api.telegram.org/").mock(return_value=httpx.Response(200))
    await notify_query(
        clean_query="¿Qué es la política?",
        latency_ms=300,
        cache_hit=False,
        pii_found=False,
        pii_types=[],
    )
    assert not route.called
