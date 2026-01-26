"""User-facing API routes for registration and lookup."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import BigInteger, cast, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.database.db_helpers import get_db_session
from src.database.models import User
from src.repositories.user_repository import UserRepository
from src.schemas.users_schema import (
    UserDetailesResponse,
    UserNotFoundResponse,
    UserSignUpErrorResponse,
    UserSignUpRequest,
    UserSignUpResponse,
)
from src.security.password import hash_password, verify_password
from src.logging import get_logger


user_router = APIRouter()
logger = get_logger(__name__)


@user_router.get(
    "/get-users-details",
    response_model=list[UserDetailesResponse] | UserNotFoundResponse,
    responses={404: {"model": UserNotFoundResponse}},
)
async def get_user_details(
    query: str | None = Query(
        default=None, description="Email or mobile number"
    ),
) -> list[UserDetailesResponse]:
    """
    Get All Users List or Specific User Based on Email or Mobile Number

    Returns:
        list[UserDetailesResponse]: User list or filtered users.
    """
    logger.debug("Fetching user details", extra={"query": query})
    # Use an async session context manager for safe cleanup.
    async with get_db_session() as session:
        stmt = select(
            User.id,
            User.name,
            User.email,
            User.mobile_number,
            User.city,
        )

        if query:
            # Determine whether the query is a mobile number or email.
            if query.isdigit():
                stmt = stmt.where(User.mobile_number == cast(int(query), BigInteger))
            else:
                stmt = stmt.where(User.email == query.lower().strip())

        result = await session.execute(stmt)
        users = result.mappings().all()

        if not users:
            # Return a structured error payload when no users match.
            logger.info("No users found for query", extra={"query": query})
            raise HTTPException(
                status_code=404,
                detail=UserNotFoundResponse(message="User not found").model_dump(),
            )

        # Convert raw mappings into response schemas.
        logger.info("Users fetched", extra={"count": len(users)})
        return [UserDetailesResponse(**user) for user in users]


@user_router.post(
    "/register-user",
    response_model=UserSignUpResponse | UserSignUpErrorResponse,
    status_code=201,
    responses={
        400: {"model": UserSignUpErrorResponse},
        409: {"model": UserSignUpErrorResponse},
        500: {"model": UserSignUpErrorResponse},
    },
)
async def sign_up_user(payload: UserSignUpRequest):
    """
    Register a new user in the system.

    Validates password confirmation, ensures uniqueness, hashes the password,
    and inserts the user record.
    """
    logger.info(
        "User signup requested",
        extra={"email": payload.email, "mobile_number": payload.mobile_number},
    )
    # 1) Password confirmation check.
    if payload.password != payload.confirm_password:
        logger.warning(
            "Password confirmation failed",
            extra={"email": payload.email, "mobile_number": payload.mobile_number},
        )
        raise HTTPException(
            status_code=400,
            detail=UserSignUpErrorResponse(
                email=payload.email,
                mobile_number=payload.mobile_number,
                message="Passwords do not match",
            ).model_dump(),
        )

    async with get_db_session() as session:
        try:
            email = payload.email.lower().strip()
            mobile_number = payload.mobile_number

            # 2) Prevent duplicate registration by email or mobile.
            existing_user = await UserRepository.get_by_email_or_mobile(
                session,
                email,
                mobile_number,
            )
            if existing_user:
                logger.warning(
                    "Duplicate user registration attempt",
                    extra={"email": email, "mobile_number": mobile_number},
                )
                raise HTTPException(
                    status_code=409,
                    detail=UserSignUpErrorResponse(
                        email=email,
                        mobile_number=mobile_number,
                        message="User already exists",
                    ).model_dump(),
                )

            # 3) Build the ORM model and hash the password.
            create_user = User(
                name=payload.name.strip() if payload.name else None,
                email=email,
                mobile_number=mobile_number,
                city=payload.city.strip() if payload.city else None,
                password_hash=hash_password(payload.password),
            )

            user = await UserRepository.create_user(session, create_user)

            # 4) Return a structured success response.
            logger.info(
                "User registration successful",
                extra={"user_id": str(user.id), "email": user.email},
            )
            return UserSignUpResponse(
                id=user.id,
                email=user.email,
                created_at=user.created_at,
                is_active=user.is_active,
                is_verified=user.is_verified,
                message="User registered successfully",
            )

        except IntegrityError:
            # Unique constraints (email/mobile) can still raise race errors.
            logger.warning(
                "User registration integrity error",
                extra={"email": payload.email, "mobile_number": payload.mobile_number},
            )
            raise HTTPException(
                status_code=409,
                detail=UserSignUpErrorResponse(
                    name=payload.name,
                    email=payload.email,
                    message="User already exists",
                ).model_dump(),
            )

        except SQLAlchemyError:
            # Generic database error handling for unexpected failures.
            logger.exception(
                "User registration failed due to database error",
                extra={"email": payload.email, "mobile_number": payload.mobile_number},
            )
            raise HTTPException(
                status_code=500,
                detail=UserSignUpErrorResponse(
                    name=payload.name,
                    email=payload.email,
                    message="Something went wrong. Please try again later.",
                ).model_dump(),
            )
