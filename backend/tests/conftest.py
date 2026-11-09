import asyncio
import os

os.environ.setdefault("POSTGRES_DB", "chargepoint_test")
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("STATION_MODE", "mock")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.base import Base
from app.db.session import SessionLocal, engine, get_redis
from app.main import app
from app.seed import seed


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_db():
    redis = get_redis()
    await redis.flushdb()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed()
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_redis():
    redis = get_redis()
    await redis.flushdb()
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def login(client: AsyncClient, email: str):
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest_asyncio.fixture
async def driver_headers(client):
    return await login(client, "driver@example.com")


@pytest_asyncio.fixture
async def operator_headers(client):
    return await login(client, "operator@example.com")


@pytest_asyncio.fixture
async def admin_headers(client):
    return await login(client, "admin@example.com")
