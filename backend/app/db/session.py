"""Async engine + session factory. Tables are created at app startup.

Migrations strategy: schema is pre-1.0 and SQLite-only, so we use
``Base.metadata.create_all`` on startup. Alembic gets introduced once the
schema needs to evolve against real user data.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import Base

engine = create_async_engine(settings.database_url)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
