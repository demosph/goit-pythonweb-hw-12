import asyncio

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from unittest.mock import AsyncMock

from main import app
from src.database.models import Base, User
from src.database.db import get_db
from src.services.auth import (
    Hash,
    create_access_token,
    create_email_token,
    create_refresh_token,
)

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "12345678",
    "role": "user",
}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_password = Hash().get_password_hash(test_user["password"])
            current_user = User(
                username=test_user["username"],
                email=test_user["email"],
                hashed_password=hash_password,
                confirmed=True,
                avatar="<https://twitter.com/gravatar>",
            )
            session.add(current_user)
            await session.commit()
            await session.refresh(current_user)
            test_user["id"] = current_user.id

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    # Dependency override

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception as err:
                print(err)
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_access_token():
    token = await create_access_token(data={"sub": test_user["username"]})
    return token


@pytest_asyncio.fixture()
async def get_refresh_token():
    token = await create_refresh_token(data={"sub": test_user["username"]})
    return token


@pytest.fixture()
def get_email_token():
    token = create_email_token(data={"sub": test_user["email"]})
    return token


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Global mock for Redis client."""
    # Create a mock Redis client
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None  # Redis cache does not exist
    mock_redis_client.set.return_value = True  # Redis cache is set

    # Change redis_client global variable
    monkeypatch.setattr("src.redis.redis_client", mock_redis_client)

    # Change get_redis function
    monkeypatch.setattr("src.redis.get_redis", lambda: mock_redis_client)

    return mock_redis_client