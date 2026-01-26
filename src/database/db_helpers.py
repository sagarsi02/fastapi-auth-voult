from src.config import settings
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from contextlib import asynccontextmanager
from typing import AsyncIterator

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DATABSE_USERNAME}:"
    f"{settings.DATABSE_PASSWORD}@{settings.DATABSE_HOST}:"
    f"{settings.DATABSE_PORT}/{settings.DATABSE_NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
