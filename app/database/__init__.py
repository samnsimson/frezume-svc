import logging
from sqlmodel import SQLModel
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config import settings


class Database:
    logger = logging.getLogger(__name__)
    database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(database_url, future=True, echo=False, pool_size=20, max_overflow=10, pool_pre_ping=True, pool_recycle=3600)
    async_session = async_sessionmaker[AsyncSession](bind=async_engine, class_=AsyncSession, expire_on_commit=False)

    @staticmethod
    async def init_db() -> None:
        async with Database.async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    @staticmethod
    async def get_session() -> AsyncGenerator[AsyncSession, None]:
        async with Database.async_session() as session:
            try: yield session
            finally: await session.close()

    @staticmethod
    async def transaction() -> AsyncGenerator[AsyncSession, None]:
        try:
            async with Database.async_session() as session:
                async with session.begin():
                    yield session
        except Exception as e:
            Database.logger.error(f"Transaction failed: {e}", exc_info=True)
            raise
