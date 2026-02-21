"""SQLAlchemy ORM models for application tables."""

import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy import (
    text,
    Index,
    String,
    Column,
    Integer,
    Boolean,
    TIMESTAMP,
    BigInteger,
    ForeignKey,
)

Base = declarative_base()


class User(Base):
    """User model mapped to the `users` table."""

    __tablename__ = "users"

    # Primary key.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    # Profile fields.
    name = Column(String(255), nullable=True)
    role = Column(String(9), default="user", nullable=False)
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


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # SHA-256 hashed refresh token
    token = Column(String, nullable=False, unique=True)

    is_revoked = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    expires_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

    # Absolute upper bound for the refresh-token family/session.
    session_expires_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

    # Optional but recommended for multi-device
    device_info = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_user_token", "user_id", "token"),
    )
