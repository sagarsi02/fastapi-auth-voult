"""Repository layer for user data access."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.database.models import User
from src.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Encapsulates user-related database operations."""

    @staticmethod
    async def get_by_email_or_mobile(
        session: AsyncSession,
        email: str,
        mobile_number: str,
    ) -> User | None:
        """Fetch a user by email or mobile number."""
        logger.debug("Fetching user by email/mobile")
        stmt = select(User).where(
            or_(
                User.email == email,
                User.mobile_number == mobile_number,
            )
        )
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
