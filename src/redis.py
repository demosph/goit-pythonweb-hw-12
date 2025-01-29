import redis.asyncio as redis
from fastapi import FastAPI, Request

redis_client = None

async def get_redis():
    """
    Returns the Redis client for the app. If the Redis client hasn't been initialized, raises a RuntimeError.

    Returns:
        redis.asyncio.Redis: The Redis client.
    """
    global redis_client
    if redis_client is None:
        raise RuntimeError("Redis is not initialized.")
    return redis_client


async def init_redis(app: FastAPI):
    """
    Initializes the Redis client for the FastAPI application.

    This function connects to the Redis server using the URL specified in the
    application's state, verifies the connection by sending a ping, and stores
    the Redis client in the application's state for future use.

    Args:
        app (FastAPI): The FastAPI application instance containing the Redis URL
        in its state.

    Raises:
        RuntimeError: If there is a connection error with the Redis server.
    """
    global redis_client
    try:
        redis_client = redis.from_url(app.state.redis_url)
        await redis_client.ping()
        app.state.redis_client = redis_client  # Store the Redis client in app.state
    except redis.ConnectionError as e:
        raise RuntimeError(f"Redis connection error: {e}")


async def close_redis():
    """
    Closes the Redis client connection.

    This function checks if the global Redis client is initialized and closes
    the connection if it exists, setting the Redis client to None afterwards.

    Raises:
        RuntimeError: If there's an error closing the Redis connection.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None