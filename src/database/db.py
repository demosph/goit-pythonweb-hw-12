import contextlib
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from src.conf.config import settings


class DatabaseSessionManager:
    def __init__(self, url: str):
        """
        Initialize the database session manager.

        Args:
            url (str): The database connection URL
        """
        self._engine: AsyncEngine = create_async_engine(
            url, pool_size=10, max_overflow=20, echo=True
        )
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Creates a new database session and yields it to the caller.

        The session is automatically rolled back if an exception occurs.
        The session is automatically closed when the context manager is exited.

        Yields:
            sqlalchemy.ext.asyncio.AsyncSession: A new database session.
        """
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

    async def close(self):
        """
        Dispose of the database engine.

        This method ensures that the database engine is properly disposed of,
        releasing any resources held by the connection pool.
        """
        if self._engine:
            await self._engine.dispose()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    FastAPI dependency that returns a database session.

    This dependency is intended to be used with FastAPI's Depends system to
    provide a database session to route handlers.

    The session is automatically rolled back if an exception occurs.
    The session is automatically closed when the context manager is exited.

    Yields:
        sqlalchemy.ext.asyncio.AsyncSession: A new database session.
    """
    async with sessionmanager.session() as session:
        yield session