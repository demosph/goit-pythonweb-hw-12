from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.redis import init_redis, close_redis
from src.conf.config import settings

from src.api import utils, contacts, auth, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    This context manager is used to manage the life cycle of the FastAPI
    application. It is responsible for initializing and closing the Redis
    connection.

    The lifespan context manager is used as a context manager in the
    FastAPI application, and is automatically called when the application
    starts and stops.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None
    """
    app.state.redis_url = settings.REDIS_URL
    await init_redis(app)
    yield
    await close_redis()

app = FastAPI(
    title="Rest API Service",
    description="Rest API Service for contacts app",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(utils.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Handles the RateLimitExceeded exception raised by the slowapi
    rate limiter.

    Returns a JSON response with a 429 status code and an error message.

    Args:
        request (Request): The request that triggered the rate limit.
        exc (RateLimitExceeded): The exception raised by the rate limiter.

    Returns:
        JSONResponse: A JSON response with a 429 status code and an error
        message.
    """
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded, try again later."},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)