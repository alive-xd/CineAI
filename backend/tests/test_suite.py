"""
tests/conftest.py + test_auth.py + test_recommendations.py + test_search.py

Test suite for CineAI backend.
Uses pytest-asyncio + httpx AsyncClient for async route testing.
SQLite in-memory DB for fast isolated tests.
"""

# ── conftest.py ────────────────────────────────────────────────────────────────
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from unittest.mock import AsyncMock, patch

from app.main import create_app
from app.core.database import Base, get_db
from app.core.redis_client import init_redis, close_redis

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """HTTP test client with mocked Redis and overridden DB session."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Mock Redis
    with patch("app.core.redis_client._redis_client") as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.ping = AsyncMock(return_value=True)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac


# ── test_auth.py ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "username": "user1", "password": "TestPass123"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json={**payload, "username": "user2"})
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "username": "loginuser",
        "password": "TestPass123",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "TestPass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "username": "wronguser",
        "password": "TestPass123",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPass999",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client):
    await client.post("/api/v1/auth/register", json={
        "email": "me@example.com",
        "username": "meuser",
        "password": "TestPass123",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "me@example.com",
        "password": "TestPass123",
    })
    token = login.json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ── test_recommendations.py ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recommendations_requires_auth(client):
    resp = await client.get("/api/v1/recommendations")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_feedback_requires_auth(client):
    import uuid
    resp = await client.post("/api/v1/recommendations/feedback", json={
        "recommendation_id": str(uuid.uuid4()),
        "action": "liked",
    })
    assert resp.status_code == 401


# ── test_search.py ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_keyword_search_requires_query(client):
    resp = await client.get("/api/v1/search")
    assert resp.status_code == 422  # Missing required query param


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_watchlist_requires_auth(client):
    resp = await client.get("/api/v1/watchlist")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_ratings_requires_auth(client):
    resp = await client.post("/api/v1/ratings", json={"movie_id": 550, "score": 4.5})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_taste_profile_requires_auth(client):
    resp = await client.get("/api/v1/profile/taste")
    assert resp.status_code == 401
