import uuid
from uuid import UUID
from jose import jwt
from src.config.settings import (
    ALGORITHM,
    PRIVATE_KEY_PATH,
    ACCESS_EXPIRE_MINUTES,
)
from datetime import datetime, timedelta, timezone


with open(PRIVATE_KEY_PATH, "r") as f:
    PRIVATE_KEY = f.read()


def create_access_token(user_id: UUID, role: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE_MINUTES)
    payload = {"user_id": str(user_id), "role": role, "type": "access", "exp": expire}
    return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: UUID,
    role: str,
    expire_at: datetime,
):
    payload = {
        "user_id": str(user_id),
        "role": role,
        "type": "refresh",
        "exp": expire_at,
        "jti": str(uuid.uuid4()),  # unique id (recommended for prod)
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)
