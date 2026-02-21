"""User-facing API routes for registration and lookup."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.config import settings
from src.logging import get_logger
from src.database.models import User, RefreshToken
from src.database.db_helpers import get_db_session
from src.repositories.user_repository import UserRepository
from src.security.password import hash_password, verify_password
from src.rules.jwt import create_access_token, create_refresh_token
from src.utils.strings import normalize_email

from src.rules.depends import (
    RefreshTokenContext,
    hash_data,
    validate_refresh_token,
    validate_access_token_and_user_exists,
)

from src.schemas.users_schema import (
    UserDetailesResponse,
    UserLogoutResponse,
    UserLogoutRequest,
    UserLoginRequest,
    UserLoginResponse,
    RefreshTokenResponse,
    UserSignUpRequest,
    UserSignUpResponse,
)


user_router = APIRouter()
logger = get_logger(__name__)


def internal_server_error_response(detail: str | dict = "Something went wrong. Please try again later.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
    )


# ====================================
#  USER DETAILS API
# ====================================
@user_router.get(
    "/me",
    response_model=UserDetailesResponse,
)
async def get_user_details(
    current_user: User = Depends(validate_access_token_and_user_exists),
) -> UserDetailesResponse:

        return UserDetailesResponse(
            id=current_user.id,
            name=current_user.name,
            role=current_user.role,
            email=current_user.email,
            mobile_number=current_user.mobile_number,
            city=current_user.city,
        )



# ====================================
#  USER SINGUP API
# ====================================
@user_router.post(
    "/register-user",
    response_model=UserSignUpResponse,
    status_code=201,
)
async def sign_up_user(payload: UserSignUpRequest):
    """
    Register a new user in the system.
    Validates input, ensures uniqueness, hashes password,
    and inserts the user record.
    """

    logger.info(
        "User signup requested",
        extra={"email": payload.email},
    )

    # 1️⃣ Password confirmation check
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Passwords do not match",
            },
        )

    async with get_db_session() as session:
        try:
            email = normalize_email(payload.email)
            mobile_number = payload.mobile_number

            # 2️⃣ Duplicate check
            existing_user = await UserRepository.get_user_data_by_email(
                session,
                email,
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": "User already exists",
                    },
                )

            # 3️⃣ Create user
            new_user = User(
                name=payload.name.strip() if payload.name else None,
                email=email,
                mobile_number=mobile_number,
                city=payload.city.strip() if payload.city else None,
                password_hash=hash_password(payload.password),
            )

            user = await UserRepository.create_user(session, new_user)

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
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "User already exists",
                },
            )

        except SQLAlchemyError:
            logger.exception("Database error during user registration")
            raise internal_server_error_response(
                {
                    "success": False,
                    "message": "Something went wrong. Please try again later.",
                }
            )


# ====================================
#  USER LOGIN API
# ====================================
@user_router.post(
    "/login-user",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
)
async def login_user(payload: UserLoginRequest):
    """
    Multi-device login with max 5 active sessions.
    """

    identifier = normalize_email(payload.email)
    logger.info("User login requested", extra={"email": identifier})

    async with get_db_session() as session:
        try:
            # --------------------------
            # 1️⃣ Fetch User
            # --------------------------
            user = await UserRepository.get_user_data_by_email(
                session,
                identifier,
                for_update=True,
            )

            if (
                user is None
                or not user.is_active
                or not verify_password(payload.password, user.password_hash)
            ):
                logger.warning("Login failed", extra={"email": identifier})
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )

            # --------------------------
            # 2️⃣ Cleanup expired tokens
            # --------------------------
            now_utc = datetime.now(timezone.utc)
            await UserRepository.revoke_expired_refresh_tokens(session, now_utc)

            # --------------------------
            # 3️⃣ Count active sessions
            # --------------------------
            active_sessions = await UserRepository.count_active_refresh_tokens(
                session=session,
                user_id=user.id,
                now_utc=now_utc,
            )

            if active_sessions >= settings.MAX_ACTIVE_DEVICES:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Maximum login limit ({settings.MAX_ACTIVE_DEVICES}) reached. Logout from another device.",
                )

            # --------------------------
            # 4️⃣ Generate Tokens
            # --------------------------
            access_token = create_access_token(user.id, user.role)
            session_expires_at = now_utc + timedelta(
                days=settings.REFRESH_SESSION_EXPIRE_DAYS
            )
            refresh_expires_at = min(
                now_utc + timedelta(
                    days=settings.REFRESH_EXPIRE_DAYS
                ),
                session_expires_at,
            )
            refresh_token = create_refresh_token(
                user.id,
                user.role,
                refresh_expires_at,
            )
            hashed_refresh_token = hash_data(refresh_token)

            expires_at = refresh_expires_at

            refresh_token_expires_in_days = max(
                0,
                int(
                    (refresh_expires_at - now_utc).total_seconds() // 86400
                ),
            )

            # --------------------------
            # 5️⃣ Insert new refresh token
            # --------------------------
            new_refresh = RefreshToken(
                user_id=user.id,
                token=hashed_refresh_token,
                is_revoked=False,
                created_at=now_utc,
                expires_at=expires_at,
                session_expires_at=session_expires_at,
                device_info=payload.device_info if hasattr(payload, "device_info") else None,
            )

            session.add(new_refresh)

            # --------------------------
            # 6️⃣ Update last login
            # --------------------------
            user.last_login_at = now_utc

            await session.commit()

            logger.info(
                "User login successful",
                extra={"user_id": str(user.id)},
            )

            return UserLoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                access_token_expires_in_seconds=settings.ACCESS_EXPIRE_MINUTES * 60,
                refresh_token_expires_in_days=refresh_token_expires_in_days,
                user={
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "message": "User logged in successfully",
                },
            )

        except HTTPException:
            raise

        except SQLAlchemyError:
            await session.rollback()
            logger.exception("Database error during login")

            raise internal_server_error_response()
    

# ====================================
#  USER LOGOUT API
# ====================================
@user_router.post("/logout-user", response_model=UserLogoutResponse)
async def logout_user(
    payload: UserLogoutRequest,
    current_user: User = Depends(validate_access_token_and_user_exists),
):
    async with get_db_session() as session:
        try:
            hashed_token = hash_data(payload.refresh_token)

            refresh_token_obj = await UserRepository.get_active_refresh_token(
                session=session,
                user_id=current_user.id,
                hashed_token=hashed_token,
            )

            if not refresh_token_obj:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or revoked refresh token",
                )

            refresh_token_obj.is_revoked = True
            await session.commit()

            return UserLogoutResponse(
                message="User logged out successfully"
            )

        except SQLAlchemyError:
            await session.rollback()
            raise internal_server_error_response("Something went wrong")


# ====================================
#  GET ACCESS TOKEN VIA REFRESH TOKEN API
# ====================================
@user_router.post(
    "/get-access-token-from-refresh-token",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def get_access_token_from_refresh_token(
    refresh_context: RefreshTokenContext = Depends(validate_refresh_token),
):
    current_user = refresh_context.user
    raw_refresh_token = refresh_context.refresh_token
    now_utc = datetime.now(timezone.utc)
    hashed_current_refresh = hash_data(raw_refresh_token)

    async with get_db_session() as session:
        try:
            current_refresh = await UserRepository.get_active_refresh_token(
                session=session,
                user_id=current_user.id,
                hashed_token=hashed_current_refresh,
                now_utc=now_utc,
                for_update=True,
            )

            if current_refresh is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or revoked refresh token",
                )

            if current_refresh.session_expires_at <= now_utc:
                current_refresh.is_revoked = True
                await session.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh session expired. Please login again.",
                )

            refresh_expires_at = min(
                now_utc + timedelta(days=settings.REFRESH_EXPIRE_DAYS),
                current_refresh.session_expires_at,
            )

            access_token = create_access_token(current_user.id, current_user.role)
            new_refresh_token = create_refresh_token(
                current_user.id,
                current_user.role,
                refresh_expires_at,
            )
            new_hashed_refresh = hash_data(new_refresh_token)

            current_refresh.is_revoked = True
            rotated_refresh = RefreshToken(
                user_id=current_user.id,
                token=new_hashed_refresh,
                is_revoked=False,
                created_at=now_utc,
                expires_at=refresh_expires_at,
                session_expires_at=current_refresh.session_expires_at,
                device_info=current_refresh.device_info,
            )
            session.add(rotated_refresh)
            await session.commit()

            refresh_token_expires_in_days = max(
                0,
                int(
                    (refresh_expires_at - now_utc).total_seconds() // 86400
                ),
            )

            return RefreshTokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                access_token_expires_in_seconds=settings.ACCESS_EXPIRE_MINUTES * 60,
                refresh_token_expires_in_days=refresh_token_expires_in_days,
            )
        except HTTPException:
            raise
        except SQLAlchemyError:
            await session.rollback()
            logger.exception("Database error during token refresh")
            raise internal_server_error_response()
