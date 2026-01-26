"""Application settings loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# Postgres database settings (required for DB connectivity).
DATABSE_NAME = os.getenv("DATABASE_NAME", "")
DATABSE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABSE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABSE_USERNAME = os.getenv("DATABASE_USERNAME", "")
DATABSE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
