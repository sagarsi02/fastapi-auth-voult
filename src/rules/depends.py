import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.database.models import User
from src.database.db_helpers import get_db_session
from src.config.settings import PUBLIC_KEY_PATH, ALGORITHM
from src.repositories.user_repository import UserRepository


security = HTTPBearer()

with open(PUBLIC_KEY_PATH, "r") as f:
    PUBLIC_SECRET_KEY = f.read()


@dataclass
class RefreshTokenContext:
    user: User
    refresh_token: str


# ---------------- HASG & VERIFY HASH ----------------


def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


# ---------------- TOKEN VERIFICATION ----------------


def decode_and_validate_token(
    token: str,
    expected_type: str,
    require_role: bool = False,
) -> dict:
    try:
        payload = jwt.decode(token, PUBLIC_SECRET_KEY, algorithms=ALGORITHM)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    if require_role and not payload.get("role"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return payload


async def access_token_verify(token: str) -> UUID:
    payload = decode_and_validate_token(token, expected_type="access")

    try:
        return UUID(payload["user_id"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token user_id",
        )


# ---------------- USER FETCH ----------------


async def get_user_data(user_id: UUID) -> User:
    async with get_db_session() as session:
        user = await UserRepository.get_user_data_by_id(session, user_id)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return user


async def validate_access_token_and_user_exists(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    user_id = await access_token_verify(token)
    user = await get_user_data(user_id)

    return user


async def validate_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> RefreshTokenContext:
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    payload = decode_and_validate_token(
        token,
        expected_type="refresh",
        require_role=True,
    )
    user_id = payload["user_id"]

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token user_id",
        )

    await check_refresh_token_revoked(token, user_uuid)
    user = await get_user_data(user_uuid)
    return RefreshTokenContext(user=user, refresh_token=token)


async def check_refresh_token_revoked(refresh_token: str, user_id: UUID):
    async with get_db_session() as session:
        now_utc = datetime.now(timezone.utc)
        hashed_token = hash_data(refresh_token)
        refresh_table_data = await UserRepository.get_active_refresh_token(
            session=session,
            user_id=user_id,
            hashed_token=hashed_token,
            now_utc=now_utc,
        )

        if refresh_table_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
            )

        return True
