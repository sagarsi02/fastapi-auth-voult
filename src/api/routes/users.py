from uuid import uuid4
from src.database.models import User
from sqlalchemy import cast, or_, select, BigInteger
from fastapi import APIRouter, HTTPException, Query
from src.database.db_helpers import get_db_session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from src.repositories.user_repository import UserRepository
from src.security.password import (
    hash_password,
    verify_password
)
from src.schemas.users_schema import (
    UserDetailesResponse,
    UserSignUpRequest,
    UserSignUpResponse,
    UserSignUpErrorResponse,
    UserNotFoundResponse,
)


user_router = APIRouter()

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
    async with get_db_session() as session:  # Use session, not connection
        stmt = select(
            User.id,
            User.name,
            User.email,
            User.mobile_number,
            User.city,
        )

        if query:
            if query.isdigit():
                stmt = stmt.where(User.mobile_number == cast(int(query), BigInteger))
            else:
                stmt = stmt.where(User.email == query.lower().strip())

        result = await session.execute(stmt)
        users = result.mappings().all()

        if not users:
            raise HTTPException(
                status_code=404,
                detail=UserNotFoundResponse(message="User not found").model_dump(),
            )

        # convert to list of Pydantic models
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
    # 1️⃣ Password check
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=400,
            detail=UserSignUpErrorResponse(
                name=payload.name,
                email=payload.email,
                message="Passwords do not match",
            ).model_dump(),
        )

    async with get_db_session() as session:
        try:
            email = payload.email.lower().strip()
            mobile_number = payload.mobile_number

            # 2️⃣ Check existing user
            existing_user = await UserRepository.get_by_email_or_mobile(
                session,
                email,
                mobile_number,
            )
            if existing_user:
                raise HTTPException(
                    status_code=409,
                    detail=UserSignUpErrorResponse(
                        email=email,
                        mobile_number=mobile_number,
                        message="User already exists",
                    ).model_dump(),
                )

            # 3️⃣ Create user
            create_user = User(
                name=payload.name.strip() if payload.name else None,
                email=email,
                mobile_number=mobile_number,
                city=payload.city.strip() if payload.city else None,
                password_hash=hash_password(payload.password),
            )

            user = await UserRepository.create_user(session, create_user)

            return UserSignUpResponse(
                id=user.id,
                email=user.email,
                created_at=user.created_at,
                is_active=user.is_active,
                is_verified=user.is_verified,
                message="User registered successfully",
            )

        except IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=UserSignUpErrorResponse(
                    name=payload.name,
                    email=payload.email,
                    message="User already exists",
                ).model_dump(),
            )

        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail=UserSignUpErrorResponse(
                    name=payload.name,
                    email=payload.email,
                    message="Something went wrong. Please try again later.",
                ).model_dump(),
            )
