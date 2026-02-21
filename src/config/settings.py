"""Application settings loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
current_PATH = os.getcwd()
current_file = Path(__file__)
BASE_DIR = current_file.parent.parent

# Postgres database settings (required for DB connectivity).
DATABSE_NAME = os.getenv("DATABASE_NAME", "")
DATABSE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABSE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABSE_USERNAME = os.getenv("DATABASE_USERNAME", "")
DATABSE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")


# JWT Config
PRIVATE_KEY_PATH = os.path.join(BASE_DIR, "keys/private_key.pem")
PUBLIC_KEY_PATH = os.path.join(BASE_DIR, "keys/public_key.pem")
ALGORITHM = os.getenv("ALGORITHM", "RS256")
ACCESS_EXPIRE_MINUTES = int(os.getenv("ACCESS_EXPIRE_MINUTES", 15))
REFRESH_EXPIRE_DAYS = int(os.getenv("REFRESH_EXPIRE_DAYS", 7))
REFRESH_SESSION_EXPIRE_DAYS = int(os.getenv("REFRESH_SESSION_EXPIRE_DAYS", 30))
SECRET_KEY = os.getenv("SECRET_KEY", "")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "")
MAX_ACTIVE_DEVICES = int(os.getenv("MAX_ACTIVE_DEVICES", 5))
