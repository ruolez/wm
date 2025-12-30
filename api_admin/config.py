import os

from dotenv import load_dotenv

load_dotenv()


DATABASE_URL1 = os.getenv("DATABASE_URL1")
sr = os.getenv("sr")
SECRET = os.getenv("SECRET")
UPLOAD_DIR = "upload/"

# CORS settings - comma-separated list of allowed origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",")
