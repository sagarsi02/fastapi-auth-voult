# 🔐 FastAPI Auth Voult

Production-style authentication boilerplate built with FastAPI + PostgreSQL + JWT (Access + Refresh) with refresh-token rotation and absolute session expiry.

---

## ✨ Features

- 👤 User signup, login, profile (`/users/me`)
- 🔑 JWT Access + Refresh token auth
- 🔄 Refresh token rotation (old refresh token revoke on use)
- ⏳ Absolute refresh session expiry (`session_expires_at`)
- 📱 Multi-device login cap (`MAX_ACTIVE_DEVICES`)
- 🧱 SQLAlchemy async + PostgreSQL
- 📜 Structured logging support

---

## 🧰 Tech Stack

- `Python 3.13+`
- `FastAPI`
- `SQLAlchemy 2.x (Async)`
- `PostgreSQL`
- `python-jose`
- `passlib + bcrypt`
- `uvicorn`

---

## 📁 Project Structure

```text
src/
  api/routes/           # API endpoints
  config/               # environment/config settings
  database/             # models + sql schema
  repositories/         # DB access layer
  rules/                # auth/jwt/dependencies
  schemas/              # request/response models
  security/             # password helpers
  utils/                # reusable utility helpers
```

---

## 🚀 Setup Guide (Step-by-Step)

### 1. Clone Project

```bash
git clone <your-repo-url>
cd fastapi-auth-voult
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

If you use `uv`:

```bash
uv sync
```

Or with `pip`:

```bash
pip install -e .
```

### 4. Configure Environment Variables

Copy and edit env:

```bash
cp sample.env .env
```

Minimum required keys in `.env`:

```env
DATABASE_NAME=auth_voult
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USERNAME=root
DATABASE_PASSWORD=root

LOG_LEVEL=DEBUG
ALGORITHM=RS256
ACCESS_EXPIRE_MINUTES=15
REFRESH_EXPIRE_DAYS=7
REFRESH_SESSION_EXPIRE_DAYS=30
MAX_ACTIVE_DEVICES=5
```

### 5. Generate RSA Keys (if not present)

```bash
mkdir -p src/keys
openssl genrsa -out src/keys/private_key.pem 2048
openssl rsa -in src/keys/private_key.pem -pubout -out src/keys/public_key.pem
```

### 6. Create Database

```sql
CREATE DATABASE auth_voult;
```

### 7. Apply Base Schema

Run complete schema from:

- `src/database/schema.sql`

You can apply from CLI:

```bash
psql -U root -d auth_voult -f src/database/schema.sql
```

### 8. Run App

```bash
uvicorn src.main:app --reload
```

Open docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Root: `http://127.0.0.1:8000/`

---

## 🗃️ SQL Queries (Complete)

## A) Fresh Database (recommended)

Use full schema file:

- `src/database/schema.sql`

This creates:

- `users` table
- `refresh_tokens` table
- indexes/triggers/extensions

## B) Existing Database Migration (manual SQL)

If your old DB does not have `session_expires_at`, run this exact migration:

```sql
BEGIN;

ALTER TABLE refresh_tokens
ADD COLUMN session_expires_at TIMESTAMP WITH TIME ZONE;

UPDATE refresh_tokens
SET session_expires_at = created_at + INTERVAL '30 days'
WHERE session_expires_at IS NULL;

ALTER TABLE refresh_tokens
ALTER COLUMN session_expires_at SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_refresh_session_expiry
ON refresh_tokens (session_expires_at);

COMMIT;
```

If you want different absolute session window, replace `INTERVAL '30 days'` accordingly.

---

## 🔄 Auth Flow (Detailed)

### 1. Signup

- Endpoint: `POST /users/register-user`
- Creates user with hashed password.

### 2. Login

- Endpoint: `POST /users/login-user`
- Validates credentials.
- Enforces max active-device session limit.
- Returns:
  - `access_token`
  - `refresh_token`
- Stores hashed refresh token in DB with:
  - `expires_at` (shorter window, e.g. 7 days)
  - `session_expires_at` (absolute window, e.g. 30 days)

### 3. Access Protected Route

- Endpoint example: `GET /users/me`
- Send `Authorization: Bearer <access_token>`

### 4. Refresh Token Rotation

- Endpoint: `POST /users/get-access-token-from-refresh-token`
- Sends current refresh token in Authorization bearer.
- System behavior:
  - locks matching token row
  - validates active + not expired + session not expired
  - revokes old refresh token
  - issues new access token + new refresh token
- Response now returns both:
  - `access_token`
  - `refresh_token`

### 5. Logout

- Endpoint: `POST /users/logout-user`
- Revokes the provided refresh token.

---

## ⏳ Expiry Rules (Important)

- `REFRESH_EXPIRE_DAYS` = per-token validity window
- `REFRESH_SESSION_EXPIRE_DAYS` = absolute session cap

Effective refresh expiry each time =

`min(now + REFRESH_EXPIRE_DAYS, session_expires_at)`

So refresh token rotates, but session still hard-expires.

---

## 🧪 Test

```bash
pytest -q
```

---

## 🛠️ Troubleshooting

- `401 Invalid or revoked refresh token`
  - old refresh token reused after rotation
  - token already revoked/expired

- `Refresh session expired. Please login again.`
  - absolute `session_expires_at` reached

- DB errors after pulling latest code
  - ensure `session_expires_at` migration applied

---

## 📜 Copyright

**© 2026 Sagar Singh. All Rights Reserved.**

This project and its source code are proprietary unless explicitly licensed otherwise by the author.
