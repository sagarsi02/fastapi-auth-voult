# FastAPI Auth Voult

A lightweight FastAPI service that provides user registration and lookup backed by PostgreSQL.
It uses async SQLAlchemy, clear route boundaries, and a simple repository layer for data access.

## Highlights

- Async FastAPI app with clean route separation
- PostgreSQL persistence via SQLAlchemy async engine
- Minimal endpoints for registering users and querying user details
- Simple env-driven configuration

## Tech Stack

- FastAPI
- SQLAlchemy (async) + asyncpg
- PostgreSQL
- uv for dependency management

## Project Structure

```
main.py
src/
  api/routes/
    users.py
    welcome.py
  config/
    settings.py
  database/
    db_helpers.py
    models.py
    schema.sql
  repositories/
    user_repository.py
  schemas/
    users_schema.py
  security/
    password.py
```

## Quickstart (uv)

### 1) Install uv

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### 2) Create and activate env

```bash
uv venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
uv sync
```

### 4) Configure environment

Create a `.env` file in the project root:

```env
DATABSE_NAME=fastapi_auth
DATABSE_HOST=localhost
DATABSE_PORT=5432
DATABSE_USERNAME=postgres
DATABSE_PASSWORD=postgres
```

Note: the variable prefix is `DATABSE_` to match the current code.

### 5) Create database schema

```bash
psql -d fastapi_auth -f src/database/schema.sql
```

### 6) Run the API

```bash
uv run uvicorn main:app --reload
```

## API Endpoints

- `GET /` - Welcome message
- `POST /users/register-user` - Register a new user
- `GET /users/get-users-details` - List all users or filter by email/mobile using `?query=`

## Documentation

- [`docs/overview.md`](docs/overview.md) - Repo overview and components
- [`docs/setup.md`](docs/setup.md) - Project setup using uv
- [`docs/project_flow.md`](docs/project_flow.md) - Request/response flow and data paths
- [`docs/development_docs.md`](docs/development_docs.md) - Long-form auth system guide

## License

MIT
