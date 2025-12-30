from sqlalchemy import create_engine

from config import DATABASE_URL1


engine = {
    "DB_admin": create_engine(DATABASE_URL1, echo=False),
}
