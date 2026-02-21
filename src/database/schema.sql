-- PostgreSQL schema for the application.
-- This file defines extensions, tables, triggers, and indexes.

-- Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;


CREATE TABLE users (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Profile
    name VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'user',

    mobile_number VARCHAR(20),
    city VARCHAR(55),

    email VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,

    -- Auditing
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Email unique (case-insensitive safe)
CREATE UNIQUE INDEX uq_users_email_lower
ON users (LOWER(email));

-- Mobile unique (only if not null)
CREATE UNIQUE INDEX uq_users_mobile
ON users (mobile_number)
WHERE mobile_number IS NOT NULL;

-- Fast lookup for active users
CREATE INDEX idx_users_active
ON users (is_active);

-- Optional: role based filtering
CREATE INDEX idx_users_role
ON users (role);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,

    user_id UUID NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,

    -- Store SHA-256 hashed refresh token
    token VARCHAR(255) NOT NULL,

    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    session_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    device_info VARCHAR(255)
);

-- Token must be globally unique
CREATE UNIQUE INDEX uq_refresh_token
ON refresh_tokens (token);

-- Fast lookup by user
CREATE INDEX idx_refresh_user
ON refresh_tokens (user_id);

-- Fast validation query
CREATE INDEX idx_refresh_user_token
ON refresh_tokens (user_id, token);

-- Expiration cleanup optimization
CREATE INDEX idx_refresh_expiry
ON refresh_tokens (expires_at);
