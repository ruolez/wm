import os
from typing import Literal
from dotenv import load_dotenv


load_dotenv()


# Core settings.
DATABASE_URL1 = os.getenv("DATABASE_URL1")
MODE = os.getenv("MODE")
sr = os.getenv("sr")
pr = os.getenv("pr")
X_TOKEN = os.getenv("X_TOKEN")
SECRET = os.getenv("SECRET")
UPLOAD_DIR = "api1/file/"
MODE: Literal["DEV", "TEST", "PROD"]

# CORS settings - comma-separated list of allowed origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",")

# SMTP-related settings.
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SENDER_EMAIL = os.getenv("SMTP_SENDER_EMAIL")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = os.getenv("SMTP_PORT", 465)

# Auth provider settings.
MAX_SESSIONS_PER_USER = os.getenv("MAX_SESSIONS_PER_USER", 3)
HARD_EXPIRATION_HOURS = os.getenv("HARD_EXPIRATION_HOURS", 36)

# Internal settings.
SCW_INDEX = int(os.getenv("SCW_INDEX", 4))