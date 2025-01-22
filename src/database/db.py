import contextlib
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from src.conf.config import settings


class DatabaseSessionManager:
    def __init__(self, url: str):
        self._engine: AsyncEngine = create_async_engine(
            url, pool_size=10, max_overflow=20, echo=True
        )
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

    async def close(self):
        if self._engine:
            await self._engine.dispose()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    async with sessionmanager.session() as session:
        yield session