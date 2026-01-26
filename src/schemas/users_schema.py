"""Pydantic request/response schemas for user endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserSignUpRequest(BaseModel):
    """Payload for user registration."""

    email: str
    password: str
    mobile_number: int
    confirm_password: str
    name: Optional[str] = None
    city: Optional[str] = None
    

class UserSignUpResponse(BaseModel):
    """Response returned after a successful registration."""

    id: UUID
    email: str
    created_at: datetime
    is_active: bool
    is_verified: bool
    message: str


class UserSignUpErrorResponse(BaseModel):
    """Standardized error response for registration failures."""

    email: str | None = None
    mobile_number: int | None = None
    message: str
    
    # Allow loading from ORM-like objects when needed.
    model_config = ConfigDict(from_attributes=True)


class UserDetailesResponse(BaseModel):
    """Response model for user detail queries."""

    id: UUID
    email: str
    name: str | None = None
    city: str | None = None
    mobile_number: int | None = None

    # Allow loading from ORM-like objects when needed.
    model_config = ConfigDict(from_attributes=True)


class UserNotFoundResponse(BaseModel):
    """Response returned when no user is found."""

    message: str
