from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserSignUpRequest(BaseModel):
    name: Optional[str] = None
    mobile_number: Optional[int] = None
    city: Optional[str] = None
    email: str
    password: str
    confirm_password: str
    

class UserSignUpResponse(BaseModel):
    id: UUID
    email: str
    created_at: datetime
    is_active: bool
    is_verified: bool
    message: str

class UserSignUpErrorResponse(BaseModel):
    email: str
    mobile_number: int
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class UserDetailesResponse(BaseModel):
    id: UUID
    email: str
    name: str | None = None
    city: str | None = None
    mobile_number: int | None = None

    model_config = ConfigDict(from_attributes=True)


class UserNotFoundResponse(BaseModel):
    message: str
