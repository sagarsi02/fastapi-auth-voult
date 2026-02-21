"""Pydantic request/response schemas for user endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import (
    Field,
    BaseModel,
    ConfigDict,
)


class UserSignUpRequest(BaseModel):
    """Payload for user registration."""

    name: str
    email: str
    password: str
    mobile_number: int
    confirm_password: str
    city: Optional[str] = None
    

class UserSignUpResponse(BaseModel):
    """Response returned after a successful registration."""

    id: UUID
    email: str
    created_at: datetime
    is_active: bool
    is_verified: bool
    message: str
    
    model_config = {
        "from_attributes": True
    }


class UserDetailesResponse(BaseModel):
    """Response model for user detail queries."""

    id: UUID
    name: str
    role: str
    email: str
    mobile_number: int
    city: str | None = None

    # Allow loading from ORM-like objects when needed.
    model_config = ConfigDict(from_attributes=True)

class UserLogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)

class UserLogoutResponse(BaseModel):
    """Response returned after a successful logout."""

    message: str



class UserNotFoundResponse(BaseModel):
    """Response returned when no user is found."""

    message: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserData(BaseModel):
    user_id: UUID
    email: str
    role: str
    message: str


class TokenMeta(BaseModel):
    token_type: str
    access_token_expires_in_seconds: int


class TokenPairResponse(TokenMeta):
    access_token: str
    refresh_token: str
    refresh_token_expires_in_days: int


class UserLoginResponse(TokenPairResponse):
    user: UserData


class RefreshTokenResponse(TokenPairResponse):
    pass


class AccessTokenResponse(TokenMeta):
    access_token: str
