"""Repository layer for user and token data access."""

from datetime import datetime
from uuid import UUID
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.database.models import RefreshToken, User
from src.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Encapsulates user-related database operations."""

    @staticmethod
    async def get_user_data_by_email(
        session: AsyncSession,
        email: str,
        for_update: bool = False,
    ) -> User | None:
        """Fetch a user by email."""
        logger.debug("Fetching user by email")
        stmt = select(User).where(User.email == email)
        if for_update:
            stmt = stmt.with_for_update()
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_data_by_id(
        session: AsyncSession,
        user_id: UUID,
    ) -> User | None:
        """Fetch a user by id."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        session: AsyncSession,
        user,
    ) -> User:
        """Persist a new user record and return the refreshed model."""
        session.add(user)
        try:
            await session.commit()
            await session.refresh(user)
            logger.info("User created successfully", extra={"user_id": str(user.id)})
            return user
        except IntegrityError:
            # Roll back on unique constraint violations.
            await session.rollback()
            logger.warning("User creation failed: integrity error")
            raise
        except Exception:
            # Roll back on unexpected database errors.
            await session.rollback()
            logger.exception("User creation failed: unexpected error")
            raise

    @staticmethod
    async def get_active_refresh_token(
        session: AsyncSession,
        user_id: UUID,
        hashed_token: str,
        now_utc: datetime | None = None,
        for_update: bool = False,
    ) -> RefreshToken | None:
        """Fetch an active refresh token row by user and token hash."""
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.token == hashed_token,
            RefreshToken.is_revoked == False,
        )
        if now_utc is not None:
            stmt = stmt.where(
                RefreshToken.expires_at > now_utc,
                RefreshToken.session_expires_at > now_utc,
            )
        if for_update:
            stmt = stmt.with_for_update()
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_expired_refresh_tokens(
        session: AsyncSession,
        now_utc: datetime,
    ) -> None:
        """Mark all expired refresh tokens as revoked."""
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.expires_at <= now_utc)
            .values(is_revoked=True)
        )

    @staticmethod
    async def count_active_refresh_tokens(
        session: AsyncSession,
        user_id: UUID,
        now_utc: datetime,
    ) -> int:
        """Count active (non-revoked, non-expired) refresh tokens for a user."""
        result = await session.execute(
            select(func.count())
            .select_from(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > now_utc,
            )
        )
        return int(result.scalar_one())
