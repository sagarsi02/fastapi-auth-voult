from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.database.models import User

class UserRepository:

    @staticmethod
    async def get_by_email_or_mobile(
        session: AsyncSession,
        email: str,
        mobile_number: str,
    ) -> User | None:
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
        session.add(user)
        try:
            await session.commit()
            await session.refresh(user)
            return user
        except IntegrityError:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise