# Project Setup (uv)

This project uses `uv` for fast, reproducible installs.

## 1) Install uv

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

## 2) Create a virtual environment

```bash
uv venv
source .venv/bin/activate
```

## 3) Install dependencies

```bash
uv sync
```

## 4) Configure environment variables

Create `.env` in the project root:

```env
DATABSE_NAME=fastapi_auth
DATABSE_HOST=localhost
DATABSE_PORT=5432
DATABSE_USERNAME=postgres
DATABSE_PASSWORD=postgres
```

## 5) Initialize the database

```bash
psql -d fastapi_auth -f src/database/schema.sql
```

## 6) Run the API

```bash
uv run uvicorn main:app --reload
```

## Optional: Run without activation

```bash
uv run uvicorn main:app --reload
```

