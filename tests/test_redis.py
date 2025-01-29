import pytest
import redis.asyncio as redis
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch

from src.redis import get_redis, init_redis, close_redis


@pytest.fixture
def mock_redis_client():
    """
    Mock Redis client for testing.
    """
    return AsyncMock()


@pytest.fixture
def app():
    """
    Mock FastAPI application instance.
    """
    app = FastAPI()
    app.state.redis_url = "redis://localhost:6379/0"
    return app


@pytest.mark.asyncio
async def test_get_redis_not_initialized():
    """
    Test get_redis raises an error if Redis is not initialized.
    """
    with patch("src.redis.redis_client", None):
        with pytest.raises(RuntimeError, match="Redis is not initialized."):
            await get_redis()


@pytest.mark.asyncio
async def test_get_redis_initialized(mock_redis_client):
    """
    Test get_redis returns the Redis client when initialized.
    """
    # Mock global Redis client
    with patch("src.redis.redis_client", mock_redis_client):
        client = await get_redis()
        assert client == mock_redis_client


@pytest.mark.asyncio
@patch("src.redis.redis.from_url")
async def test_init_redis_success(mock_from_url, app, mock_redis_client):
    """
    Test init_redis initializes Redis successfully.
    """
    # Mock Redis client behavior
    mock_from_url.return_value = mock_redis_client
    mock_redis_client.ping.return_value = True

    await init_redis(app)

    # Assertions
    mock_from_url.assert_called_once_with(app.state.redis_url)
    mock_redis_client.ping.assert_awaited_once()
    assert app.state.redis_client == mock_redis_client


@pytest.mark.asyncio
@patch("src.redis.redis.from_url")
async def test_init_redis_connection_error(mock_from_url, app):
    """
    Test init_redis raises RuntimeError if Redis connection fails.
    """
    # Simulate connection error
    mock_from_url.side_effect = redis.ConnectionError("Connection failed")

    with pytest.raises(RuntimeError, match="Redis connection error: Connection failed"):
        await init_redis(app)


@pytest.mark.asyncio
async def test_close_redis_not_initialized():
    """
    Test close_redis does nothing if Redis is not initialized.
    """
    # Ensure redis_client is None
    with patch("src.redis.redis_client", None):
        await close_redis()  # Should not raise any errors


@pytest.mark.asyncio
async def test_close_redis_initialized(mock_redis_client):
    """
    Test close_redis closes the Redis connection when initialized.
    """
    # Mock global Redis client
    with patch("src.redis.redis_client", mock_redis_client):
        await close_redis()

        # Assertions
        mock_redis_client.close.assert_awaited_once()
        assert mock_redis_client is not None
