from datetime import datetime, timedelta
import copy
import json
import os
import pickle
import re
import pandas as pd
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, relationship, backref
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete


from .config import DATABASE_URL1, X_TOKEN, SCW_INDEX
from api1.users.model import (
    AccountNo_crons_admin,
    AdminDBs_admin,
    CreditMemos_tbl,
    CreditMemosDetails_tbl,
    ManualInventoryUpdate,
    QuotationDetailsTest,
    QuotationTest,
    QuotationsTemp,
    Quotations_tbl,
    Customers_tbl,
    Quotation,
    Items_tbl,
    Units_tbl,
    QuotationsDetails_tbl,
    QuotationDetails,
    Invoices_tbl,
    Employees_tbl,
    InvoicesDetails_tbl,
    shed_admin,
)

from sqlalchemy import (
    Integer,
    Column,
    String,
    cast,
    func,
    inspect,
    or_,
    and_,
    true,
    false,
    select,
    insert,
    update,
    join,
    delete,
    text,
)


def checking_str(val):
    if type(val) == bool:
        return "bool"
    dType = "str"
    try:
        float(val)
        dType = "float"
        if str(int(val)) == str(val):
            dType = "int"
    except:
        pass
    return dType


engine = {
    "DB_admin": create_engine(
        DATABASE_URL1, echo=True, pool_size=500, max_overflow=900
    ),
}
engine_nick = dict()
engine_nick_name = dict()
engine_name_nick = dict()
engine_name_db = dict()
engine_db_nick_name = dict()
engine_use_client_side = dict()  # {Nick: True/False} - True = use client-side pagination


def extract_ip_from_url(url):
    """Extract IP/hostname from connection string like mssql+pyodbc://user:pass@IP\\instance:port/db"""
    if not url:
        return None
    match = re.search(r'@([^\\/:]+)', url)
    return match.group(1) if match else None


# Extract DB_admin IP for comparison with other databases
# This will be used to determine if a database is on the same server as DB_admin
db_admin_ip = extract_ip_from_url(DATABASE_URL1) if DATABASE_URL1 else None

data_f = {
    "cm": "log_check_CreditMemos",
    "cq": "log_check_new_quotation",
    "sv": "log_sync_invoices",
}
time_now_5h_log = (datetime.today() - timedelta(hours=5)).strftime("%m-%d-%Y %H:%M:%S")

list_ship = [
    "shipping",
    "SIMPINSUR1",
    "ship",
    "shipment",
    "shipping",
    "simpinsur",
]
l_sku = ["NVDPROTECTION"]


def gen_config():
    with Session(engine["DB_admin"]) as session:
        stmt_select_insert_alias = select(AdminDBs_admin.__table__.columns)
        rows = session.execute(stmt_select_insert_alias).mappings().all()
        ans_list = []
        for count, i in enumerate(rows):
            ans_list.append(i["Nick"])
            pass_temp = i["Password"].replace("@", ("%40"))
            globals()[
                f"DATABASE_URL{count + 1}"
            ] = f"mssql+pyodbc://{i['Username']}:{pass_temp}@{i['ipAddress']}\\{i['ShareName']}:{i['Port']}/{i['NameDB']}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=Yes&Encrypt=no&MARS_Connection=Yes"
            engine.update(
                {
                    f"DB{count + 1}": create_engine(
                        f"mssql+pyodbc://{i['Username']}:{pass_temp}@{i['ipAddress']}\\{i['ShareName']}:{i['Port']}/{i['NameDB']}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=Yes&Encrypt=no&MARS_Connection=Yes",
                        echo=True,
                        pool_size=500,
                        max_overflow=900,
                    ),
                }
            )
            engine_nick.update({i["Nick"]: f"DB{count + 1}"})
            engine_nick_name.update({i["Nick"]: i["NameDB"]})
            engine_name_nick.update({i["NameDB"]: i["Nick"]})
            engine_name_db.update({i["NameDB"]: f"DB{count + 1}"})
            engine_db_nick_name.update({f"DB{count + 1}": i["Nick"]})
            # Compare database IP with DB_admin IP to determine pagination mode
            # True = use client-side pagination (different server, can't access DB_admin)
            # If db_admin_ip is None, default to False (server-side) to maintain existing behavior
            if db_admin_ip is not None:
                engine_use_client_side[i["Nick"]] = (i["ipAddress"] != db_admin_ip)
            else:
                engine_use_client_side[i["Nick"]] = False  # Default to server-side if can't determine
        return ans_list


def abs_path(data):
    nm = data_f[f"{data}"]
    script_dir = os.path.dirname(__file__)
    rel_path = "logs/"
    fpath = os.path.join(script_dir, f"{rel_path}{nm}.log")
    return fpath


def SEARCH_IN_DICT_VALUE_RETURN_KEY(dict_data, value):
    for i in dict_data.keys():
        if value == dict_data[i]:
            return i


def pd_req(query: str, db: str, error=None):
    df = pd.read_sql(query, engine[db])
    answ_invoice = df.to_dict("records")
    return answ_invoice


# Initialize database engines gracefully - allow app to start without external DBs configured
try:
    gen_config()
    print("Database configuration loaded successfully")
except Exception as e:
    print(f"Warning: Could not load database configuration: {e}")
    print("App starting in setup mode - configure databases via /admin")
    # Create placeholder engines for DB1-DB4 if they don't exist
    for i in range(1, 5):
        if f"DB{i}" not in engine:
            engine[f"DB{i}"] = engine["DB_admin"]  # Fallback to admin DB


Base_admin = declarative_base()
Base = declarative_base()
Base2 = declarative_base()
Base3 = declarative_base()
Base4 = declarative_base()
metadata = MetaData()

Session0 = sessionmaker(bind=engine["DB_admin"])
Session1 = sessionmaker(bind=engine.get("DB1", engine["DB_admin"]))
Session2 = sessionmaker(bind=engine.get("DB2", engine["DB_admin"]))
Session3 = sessionmaker(bind=engine.get("DB3", engine["DB_admin"]))
Session4 = sessionmaker(bind=engine.get(f"DB{SCW_INDEX}", engine["DB_admin"]))

# Create session instances (with graceful fallback)
try:
    session0 = Session0()
    session1 = Session1()
    session2 = Session2()
    session3 = Session3()
    session4 = Session4()
except Exception as e:
    print(f"Warning: Could not create database sessions: {e}")
    session0 = session1 = session2 = session3 = session4 = None

def query_f(engine, query):
    with Session(engine) as session:
        rows = session.execute(text(query)).all()
        return rows
