import pytest
import json
import sys, os

from .. import engine, engine_test
from ..config import DATABASE_URL1, DATABASE_URL_TEST, MODE
from sqlalchemy import select, insert, delete, inspect
from sqlalchemy.orm import sessionmaker, Session

from ..users.model import (
    Base,
    AdminUserProject_admin,
    AdminDBs_admin,
)

@pytest.fixture(scope="session", autouse=True)
def prepare_datbase():
    assert MODE == "TEST"

    Base.metadata.drop_all(engine_test)
    Base.metadata.create_all(engine_test)


    def open_mock_json():
        with open(
            "api1/tests/mock_AdminDBs_admin.json", encoding="utf-8", errors="ignore"
        ) as json_data:
            data = json.load(json_data, strict=False)
            return data
    DBS = open_mock_json()
    with Session(engine_test) as session:
        add_DBS = insert(AdminDBs_admin).values(DBS)
        answ_add_DBS = session.execute(add_DBS)
        session.commit()










