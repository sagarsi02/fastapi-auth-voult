import os
from dotenv import load_dotenv

load_dotenv()

# Postgres DataBase is mandatory
DATABSE_NAME = os.getenv("DATABSE_NAME", "")
DATABSE_HOST = os.getenv("DATABSE_HOST", "localhost")
DATABSE_PORT = os.getenv("DATABSE_PORT", "5432")
DATABSE_USERNAME = os.getenv("DATABSE_USERNAME", "")
DATABSE_PASSWORD = os.getenv("DATABSE_PASSWORD", "")
