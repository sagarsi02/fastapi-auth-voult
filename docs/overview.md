# Repository Overview

This project is a compact FastAPI service that exposes user registration and user lookup APIs.
The codebase is intentionally small and is organized around routes, schemas, repositories, and
async database helpers for PostgreSQL.

## Core Components

- **API routes**: HTTP endpoints in `src/api/routes/`
- **Schemas**: Pydantic request/response models in `src/schemas/`
- **Repositories**: Database operations in `src/repositories/`
- **Database**: Async engine, models, and SQL schema in `src/database/`
- **Security**: Password hashing and verification helpers in `src/security/`

## Key Endpoints

- `GET /` - Welcome/health landing
- `POST /users/register-user` - Register a user (name, email, mobile, city, password)
- `GET /users/get-users-details` - List users, optional `?query=` for email or mobile

## Data Model

`users` table fields (see `src/database/schema.sql`):

- `id` (UUID, primary key)
- `name`, `email`, `mobile_number`, `city`
- `password_hash`
- `is_active`, `is_verified`
- `last_login_at`, `created_at`, `updated_at`

## Configuration

Environment variables are read from `.env` via `python-dotenv` and must match the current
settings in `src/config/settings.py`.

