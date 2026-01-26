"""SQLAlchemy ORM models for application tables."""

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    String,
    TIMESTAMP,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """User model mapped to the `users` table."""

    __tablename__ = "users"

    # Primary key.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    # Profile fields.
    name = Column(String(255), nullable=True)
    mobile_number = Column(BigInteger, nullable=True, unique=True)
    city = Column(String(55), nullable=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String, nullable=False)

    # Status flags.
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)

    # Auditing timestamps.
    last_login_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"), onupdate=text("NOW()"))
