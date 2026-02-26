"""Async database helpers for engine and session management."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings
from src.logging import get_logger

# Logger for database operations.
logger = get_logger(__name__)

# Build the async database URL from environment settings.
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DATABSE_USERNAME}:"
    f"{settings.DATABSE_PASSWORD}@{settings.DATABSE_HOST}:"
    f"{settings.DATABSE_PORT}/{settings.DATABSE_NAME}"
)

# Log DB connection target without credentials.
logger.info(
    "Configuring database engine for %s:%s/%s",
    settings.DATABSE_HOST,
    settings.DATABSE_PORT,
    settings.DATABSE_NAME,
)

# Create the async SQLAlchemy engine.
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# Factory for creating new async sessions.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield an async session with automatic cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Database session opened")
            yield session
            logger.debug("Database session closing")
        except HTTPException:
            # HTTP exceptions are expected control flow from route handlers.
            raise
        except Exception:
            logger.exception("Database session error")
            raise
        finally:
            await session.close()
