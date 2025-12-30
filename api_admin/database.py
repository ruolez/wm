from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, relationship, backref
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete, update, and_

from sqlalchemy import text

from config import DATABASE_URL1


engine = {
    "DB_admin": create_engine(DATABASE_URL1, echo=True),
}

Base_admin = declarative_base()
Base = declarative_base()
Base2 = declarative_base()
Base3 = declarative_base()
Base4 = declarative_base()
metadata = MetaData()

Session0 = sessionmaker(bind=engine["DB_admin"])
session0 = Session0()


def query_f(engine, query):
    print("testtttttt_func")
    with Session(engine) as session:
        print(query, "ioiiiiiiiiiiiii")
        rows = session.execute(query).scalar()  # ok
        if rows is not None:
            return vars(rows)
