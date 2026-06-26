"""Tests for /auth — registro, login y /me."""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.document import Document  # noqa: F401 — register table
from app.models.user import User  # noqa: F401 — register table


@pytest.fixture
async def db_session(tmp_path):
    db_file = str(tmp_path / "test.db")
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

    from app.api.routers import auth
    from app.models.database import get_db

    app = FastAPI()
    app.include_router(auth.router)

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_register_success(client: AsyncClient) -> None:
    resp = await client.post("/auth/register", json={"email": "a@b.cl", "password": "secret12"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "a@b.cl"
    assert data["access_token"]


async def test_register_duplicate_email(client: AsyncClient) -> None:
    await client.post("/auth/register", json={"email": "dup@b.cl", "password": "secret12"})
    resp = await client.post("/auth/register", json={"email": "dup@b.cl", "password": "secret12"})
    assert resp.status_code == 409


async def test_register_weak_password(client: AsyncClient) -> None:
    resp = await client.post("/auth/register", json={"email": "c@b.cl", "password": "short"})
    assert resp.status_code == 400


async def test_login_success_and_me(client: AsyncClient) -> None:
    await client.post("/auth/register", json={"email": "d@b.cl", "password": "secret12"})
    resp = await client.post("/auth/login", json={"email": "d@b.cl", "password": "secret12"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "d@b.cl"


async def test_login_wrong_password_is_generic(client: AsyncClient) -> None:
    await client.post("/auth/register", json={"email": "e@b.cl", "password": "secret12"})
    resp = await client.post("/auth/login", json={"email": "e@b.cl", "password": "wrongpass1"})
    assert resp.status_code == 401


async def test_login_unknown_email_is_generic(client: AsyncClient) -> None:
    resp = await client.post("/auth/login", json={"email": "nope@b.cl", "password": "secret12"})
    assert resp.status_code == 401


async def test_me_without_token_is_401(client: AsyncClient) -> None:
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_account_lockout_after_repeated_failures(client: AsyncClient) -> None:
    await client.post("/auth/register", json={"email": "lock@b.cl", "password": "secret12"})
    # 5 intentos fallidos permitidos, el 6º queda bloqueado (429).
    for _ in range(5):
        r = await client.post("/auth/login", json={"email": "lock@b.cl", "password": "mala1234"})
        assert r.status_code == 401
    blocked = await client.post("/auth/login", json={"email": "lock@b.cl", "password": "mala1234"})
    assert blocked.status_code == 429
