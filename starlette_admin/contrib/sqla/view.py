from typing import Any, Dict, List, Optional, Sequence, Type, Union
import datetime
import pandas as pd
import urllib.parse
import sys
import os
import math
from urllib.parse import parse_qsl
import anyio.to_thread
from api1.api_v2.utils import get_time_range_limit
from sqlalchemy import (
    Column,
    String,
    cast,
    func,
    inspect,
    or_,
    and_,
    select,
    update,
    asc,
    desc,
)

from sqlalchemy.exc import NoInspectionAvailable, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, Mapper, Session, joinedload
from sqlalchemy.sql import Select, text

from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.contrib.sqla.converters import (
    BaseSQLAModelConverter,
    ModelConverter,
)
from starlette_admin.contrib.sqla.exceptions import InvalidModelError
from starlette_admin.contrib.sqla.handlers import InvoiceHandler
from starlette_admin.contrib.sqla.helpers import (
    build_order_clauses,
    build_query,
    extract_column_python_type,
    matches_allowed_status,
    normalize_list,
    USERS_STATUS_LIST,
)
from starlette_admin.exceptions import ActionFailed, FormValidationError
from starlette_admin.fields import (
    ColorField,
    EmailField,
    FileField,
    PhoneField,
    RelationField,
    StringField,
    TextAreaField,
    URLField,
)
from starlette_admin.helpers import prettify_class_name, slugify_class_name
from starlette_admin.views import BaseModelView

from sqlalchemy.orm import Session

from api1.users.model import (
    AccountSyncSetting,
    Quotation,
    QuotationDetails,
    AdminDBs_admin,
    Customers_tbl,
    Items_tbl,
    QuotationsTemp,
    Quotations_tbl,
    Employees_tbl,
    QuotationsDetails_tbl,
    AdminUserProject_admin,
    InvoicesDetails_tbl,
    Invoices_tbl,
    Shippers_tbl,
    Terms_tbl,
)

sys.path.append(os.getcwd())
from api1 import (
    session1,
    session2,
    session3,
    session0,
    session4,
    query_f,
    engine,
    engine_nick,
    engine_nick_name,
    engine_name_nick,
    engine_name_db,
    engine_db_nick_name,
    SCW_INDEX,
)

session_list = [session1, session2, session3, session4]

# Count of active databases to collaborate with. Should be in sync with session_list. 
ACTIVE_DB_COUNT = len(session_list)

def no_null(value):
    if isinstance(value, str):
        value = value.replace("'", "''")
        value = f"'{value}'"
    if value == None:
        value = "NULL"
    return value


def no_null_manuid(value):
    if isinstance(value, str):
        value = value.replace("'", "''")
        value = f"'{value}'"
    if value == None:
        value = 0
    return value


def no_null_categ(value):
    print(value, "valueeeee")
    if isinstance(value, str):
        val = value.split("_")[0]
        val1 = value.split("_")[1]
    if value == None:
        val = 0
        val1 = 0
    return val, val1


def mod_value(val):
    if isinstance(val, str):
        val = val.replace("'", "''")
    if (isinstance(val, str) and not val) or (isinstance(val, list) and not val):
        return "''"
    elif val == None:
        return "NULL"
    elif isinstance(val, float) and math.isnan(float(val)):
        return 0.0
    elif val == False:
        return 0
    elif val == True:
        return 1
    elif isinstance(val, int) or isinstance(val, float):
        return val
    else:
        return f"{val}"


def SEARCH_IN_DICT_VALUE_RETURN_KEY(dict_data, value):
    for i in dict_data.keys():
        if value == dict_data[i]:
            return i


column_list_date = ["LastSold", "LastCountDate", "ExpDate", "LastReceived"]
column_list_str = [
    "ExtDescription",
    "ManuProductID",
    "SPPromotionDescription",
    "SPPromotionCode",
    "ProductMessage",
    "Notes",
]
column_list_zero = [
    "UnitPriceA",
    "UnitPriceB",
    "UnitPriceC",
    "MSRPrice",
    "AvrCost",
    "LastCost",
    "LastReceived",
    "ReorderLevel",
    "ReorderQuant",
    "QuantOnHand",
    "QuantOnOrder",
    "PromotionID",
    "SPPromoted",
    "StLocationID",
    "Discontinued",
    "UnitID2",
    "UnitID3",
    "UnitID4",
    "UnitQty2",
    "UnitQty3",
    "UnitQty4",
    "UnitPrice2",
    "UnitPriceA2",
    "UnitPriceB2",
    "UnitPriceC2",
    "UnitPrice3",
    "UnitPriceA3",
    "UnitPriceB3",
    "UnitPriceC3",
    "UnitPrice4",
    "UnitPriceA4",
    "UnitPriceB4",
    "UnitPriceC4",
    "ItemWeight",
    "BarcodeFormat",
]
column_list_one = ["ValuationMethod", "ProductType"]

cate_dif_db = [
    "CateID1",
    "CateID2",
    "CateID3",
    "CateID4",
    "ManuID1",
    "ManuID2",
    "ManuID3",
    "UnitCost1",
    "UnitCost2",
    "UnitCost3",
    "UnitPrice11",
    "UnitPrice21",
    "UnitPrice31",
    "UnitID11",
    "UnitID21",
    "UnitID31",
    "TaxID11",
    "TaxID21",
    "TaxID31",
    "TAXID41",
]

miss_list = ["CateID", "ManufacturerID", "UnitCost", "UnitPrice", "SubCateID"]


def session_init(request):
    request_list = request.path_params["identity"].split("_")

    print(request_list, "request.path_params_vieww__session_init________")
    if "db2" in request_list:
        session: Union[Session, AsyncSession] = session2
    elif "db3" in request_list:
        session: Union[Session, AsyncSession] = session3
    elif "db4" in request_list:
        session: Union[Session, AsyncSession] = session4
    elif "admin" in request_list:
        session: Union[Session, AsyncSession] = session0
    else:
        session: Union[Session, AsyncSession] = session1
    return session


def gen_name():
    query = """SELECT [id]
		,[TypeDB]
		,[Username]
		,[Password]
		,[ipAddress]
		,[ShareName]
		,[Port]
		,[NameDB]
		,[Nick]
	FROM [DB_admin].[dbo].[AdminDBs_admin]"""
    with Session(engine["DB_admin"]) as session:
        rows = session.execute(text(query)).all()  # ok
        ans_list = []
        for i in rows:
            print(i)
            ans_list.append(i[-1])
        return ans_list


def get_status_filtered_ids(
    cutoff: datetime.datetime,
    status_filters: List[str],
) -> set:
    """
    Query DB_admin to get Dop1 values matching status filters.
    Used for cross-server status filtering when SQL JOIN is not possible.
    """
    if not status_filters:
        return set()

    # Handle "Converted" separately - determined by AutoOrderNo, not DB_admin
    non_converted = [s for s in status_filters if s.upper() != "CONVERTED"]
    if not non_converted:
        return set()  # Only "Converted" filter - handled in SQL via AutoOrderNo

    status_sql = "', '".join([s.replace("'", "''") for s in non_converted])
    query = f"""
        SELECT DISTINCT Dop1
        FROM [DB_admin].[dbo].[QuotationsStatus]
        WHERE Status IN ('{status_sql}')
          AND DateCreate > '{cutoff.strftime('%Y-%m-%d %H:%M:%S')}'
    """

    with Session(engine["DB_admin"]) as admin_session:
        result = admin_session.execute(text(query)).scalars().all()
        return set(str(dop1) for dop1 in result if dop1 is not None)


def batch_lookup_status(quotation_ids: List[str]) -> Dict[str, str]:
    """
    Batch lookup status for given QuotationIDs from DB_admin.
    Returns dict mapping QuotationID (as string) -> Status.
    Used for enrichment when cross-DB JOIN is not possible.
    """
    if not quotation_ids:
        return {}

    status_map = {}
    chunk_size = 500

    with Session(engine["DB_admin"]) as admin_session:
        for i in range(0, len(quotation_ids), chunk_size):
            chunk = quotation_ids[i:i + chunk_size]
            ids_sql = "', '".join(str(qid).replace("'", "''") for qid in chunk)
            query = f"""
                SELECT Dop1, Status
                FROM [DB_admin].[dbo].[QuotationsStatus]
                WHERE Dop1 IN ('{ids_sql}')
            """
            results = admin_session.execute(text(query)).mappings().all()
            for row in results:
                status_map[str(row['Dop1'])] = row['Status']

    return status_map


class ModelView(BaseModelView):
    def __init__(
        self,
        model: Type[Any],
        icon: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        identity: Optional[str] = None,
        converter: Optional[BaseSQLAModelConverter] = None,
        view_table: Optional[bool] = True,
    ):
        try:
            mapper: Mapper = inspect(model)  # type: ignore
        except NoInspectionAvailable:
            raise InvalidModelError(  # noqa B904
                f"Class {model.__name__} is not a SQLAlchemy model."
            )
        assert len(mapper.primary_key) == 1, (
            "Multiple PK columns not supported, A possible solution is to override "
            "BaseModelView class and put your own logic "
        )
        self.model = model
        self.identity = (
            identity or self.identity or slugify_class_name(self.model.__name__)
        )
        self.label = (
            label or self.label or prettify_class_name(self.model.__name__) + "s"
        )
        self.name = name or self.name or prettify_class_name(self.model.__name__)
        self.icon = icon
        self._pk_column: Column = mapper.primary_key[0]
        self.pk_attr = self._pk_column.key
        self._pk_coerce = extract_column_python_type(self._pk_column)
        if self.fields is None or len(self.fields) == 0:
            self.fields = [
                self.model.__dict__[f].key
                for f in self.model.__dict__
                if type(self.model.__dict__[f]) is InstrumentedAttribute
            ]
        self.fields = (converter or ModelConverter()).convert_fields_list(
            fields=self.fields, model=self.model, mapper=mapper
        )
        self.exclude_fields_from_list = normalize_list(self.exclude_fields_from_list)  # type: ignore
        self.exclude_fields_from_detail = normalize_list(
            self.exclude_fields_from_detail
        )  # type: ignore
        self.exclude_fields_from_create = normalize_list(
            self.exclude_fields_from_create
        )  # type: ignore
        self.exclude_fields_from_edit = normalize_list(self.exclude_fields_from_edit)  # type: ignore
        _default_list = [
            field.name
            for field in self.fields
            if not isinstance(field, (RelationField, FileField))
        ]
        self.searchable_fields = normalize_list(
            self.searchable_fields
            if (self.searchable_fields is not None)
            else _default_list
        )
        self.sortable_fields = normalize_list(
            self.sortable_fields
            if (self.sortable_fields is not None)
            else _default_list
        )
        self.export_fields = normalize_list(self.export_fields)
        self.fields_default_sort = normalize_list(
            self.fields_default_sort, is_default_sort_list=True
        )
        super().__init__()

    async def handle_action(
        self, request: Request, pks: List[Any], name: str
    ) -> Union[str, Response]:
        try:
            return await super().handle_action(request, pks, name)
        except SQLAlchemyError as exc:
            raise ActionFailed(str(exc)) from exc

    def get_list_query(self) -> Select:
        q = select(self.model)
        return q

    def get_count_query(self) -> Select:
        return select(func.count(self._pk_column))

    def get_search_query(self, request: Request, term: str) -> Any:
        clauses = []
        for field in self.fields:
            if field.searchable and type(field) in [
                StringField,
                TextAreaField,
                EmailField,
                URLField,
                PhoneField,
                ColorField,
            ]:
                attr = getattr(self.model, field.name)
                clauses.append(cast(attr, String).ilike(f"%{term}%"))
        return or_(*clauses)

    async def count(
        self,
        request: Request,
        where: Union[Dict[str, Any], str, None] = None,
    ) -> int:
        session = session_init(request)

        active_table = request.path_params["identity"]
        if active_table == "quotation":
            session: Union[Session, AsyncSession] = session0

        stmt = self.get_count_query()
        if where is not None:
            if isinstance(where, dict):
                where = build_query(where, self.model)
            else:
                where = await self.build_full_text_search_query(
                    request, where, self.model
                )
            stmt = stmt.where(where)  # type: ignore
        if isinstance(session, AsyncSession):
            return (await session.execute(text(stmt))).scalar_one()
        return (await anyio.to_thread.run_sync(session.execute, stmt)).scalar_one()

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        model_dop: Type[Any] = None,
        query_url: Optional[str] = None,
    ) -> Sequence[Any]:
        if model_dop != None:
            self.model = model_dop
        user_account = request.state.user["name"].strip().lower()
        user_account_status = request.state.user["statususer"].strip().lower()
        print(user_account_status, "user_account_statussssss")
        stmt = self.get_list_query().offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        if where is not None:
            if isinstance(where, dict):
                where = build_query(where, self.model)
            else:
                where = await self.build_full_text_search_query(
                    request, where, self.model
                )
            stmt = stmt.where(where)
        order_by = []
        stmt_str = (
            str(stmt).split(" ")[1].split(".")[1].replace('"', "").replace(",", "")
            + " asc"
        )
        order_by.append(stmt_str)
        stmt = stmt.order_by(*build_order_clauses(order_by, self.model))
        active_table = request.path_params["identity"]

        if active_table == "quotation":
            url_ref: str = ""
            order_by: str = ""
            for i in range(len(request.scope["headers"])):
                if len(request.scope["headers"][i]) > 1:
                    for i1 in request.scope["headers"][i]:
                        if isinstance(i1, bytes):
                            val_i = i1.decode()
                        else:
                            val_i = i1
                        if val_i == "referer":
                            url_ref = request.scope["headers"][i][1]

            query_string = urllib.parse.unquote_plus(
                request.__dict__["scope"]["query_string"].decode("utf-8")
            )
            query_string_dict = dict(parse_qsl(query_string))
            session: Union[Session, AsyncSession] = session0
            time_now_1d = (
                datetime.datetime.today() - datetime.timedelta(days=1)
            ).strftime("%m-%d-%Y %H:%M:%S")
            if "manager" in user_account_status.split("/"):
                cutoff = datetime.datetime.utcnow() - datetime.timedelta(weeks=get_time_range_limit())
                stmt_quotation = (
                    select(Quotation.__table__.columns)
                    .where(
                        or_(
                            Quotation.LastUpdate > time_now_1d,
                            Quotation.Status != "CANCEL",
                        ),
                        and_(Quotation.InvoiceNumber != None),
                    )
                    .filter(
                        Quotation.DateCreate > cutoff,
                    )
                    .limit(limit)
                    .offset(skip)
                )

                if "order_by" in query_string_dict:
                    list_order_by: list[str] = query_string_dict["order_by"].split(" ")
                    if list_order_by[1] == "asc":
                        stmt_quotation = stmt_quotation.order_by(asc(list_order_by[0]))
                    elif list_order_by[1] == "desc":
                        stmt_quotation = stmt_quotation.order_by(desc(list_order_by[0]))
                else:
                    stmt_quotation = stmt_quotation.order_by(
                        Quotation.DateCreate.desc()
                    )
                answ_quotation = session.execute(stmt_quotation).mappings().all()
                return answ_quotation
            if matches_allowed_status(user_account_status, USERS_STATUS_LIST):
                stmt_quotation = (
                    select(Quotation.__table__.columns)
                    .where(
                        or_(
                            Quotation.LastUpdate > time_now_1d,
                            Quotation.Status != "CANCEL",
                        ),
                        and_(Quotation.InvoiceNumber != None),
                    )
                    .filter(Quotation.SalesRepresentative.like(user_account))
                    .limit(limit)
                    .offset(skip)
                )

                if "order_by" in query_string_dict:
                    list_order_by: list[str] = query_string_dict["order_by"].split(" ")
                    if list_order_by[1] == "asc":
                        stmt_quotation = stmt_quotation.order_by(asc(list_order_by[0]))
                    elif list_order_by[1] == "desc":
                        stmt_quotation = stmt_quotation.order_by(desc(list_order_by[0]))
                else:
                    stmt_quotation = stmt_quotation.order_by(
                        Quotation.DateCreate.desc()
                    )
                answ_quotation = session.execute(stmt_quotation).mappings().all()
                return answ_quotation
        elif active_table == "quotations1_tbl":
            url_ref: str = ""
            order_by: str = ""
            for i in range(len(request.scope["headers"])):
                if len(request.scope["headers"][i]) > 1:
                    for i1 in request.scope["headers"][i]:
                        if isinstance(i1, bytes):
                            val_i = i1.decode()
                        else:
                            val_i = i1
                        if val_i == "referer":
                            url_ref = request.scope["headers"][i][1]
            query_string = urllib.parse.unquote_plus(
                request.__dict__["scope"]["query_string"].decode("utf-8")
            )
            query_string_dict = dict(parse_qsl(query_string))
            with Session(engine["DB_admin"]) as session:
                query_quotations1_tbl = select(QuotationsTemp.__table__.columns).filter(
                    QuotationsTemp.SessionID.like(user_account)
                )
                if "order_by" in query_string_dict:
                    list_order_by: list[str] = query_string_dict["order_by"].split(" ")
                    if list_order_by[1] == "asc":
                        query_quotations1_tbl = query_quotations1_tbl.order_by(
                            asc(list_order_by[0])
                        )
                    elif list_order_by[1] == "desc":
                        query_quotations1_tbl = query_quotations1_tbl.order_by(
                            desc(list_order_by[0])
                        )
                else:
                    query_quotations1_tbl = query_quotations1_tbl.order_by(
                        QuotationsTemp.id.desc()
                    )
                answ_quotation = session.execute(query_quotations1_tbl).mappings().all()
            return answ_quotation
        elif active_table == "quotations2_tbl":
            url_ref = ""
            for hdr in request.scope["headers"]:
                name = hdr[0].decode() if isinstance(hdr[0], bytes) else hdr[0]
                if name == "referer":
                    url_ref = hdr[1].decode() if isinstance(hdr[1], bytes) else hdr[1]

            query_string = urllib.parse.unquote_plus(
                request.scope["query_string"].decode("utf-8")
            )
            query_string_dict = dict(parse_qsl(query_string))

            # Debug: Log received filters
            sales_rep_filters = [v for k, v in parse_qsl(query_string) if k == "sales_rep"]
            status_filters = [v for k, v in parse_qsl(query_string) if k == "status"]
            order_by_list = [v for k, v in parse_qsl(query_string) if k == "order_by"]
            print(f"🔍 FILTERS RECEIVED: sales_rep={sales_rep_filters}, status={status_filters}, order_by={order_by_list}")

            with Session(engine["DB_admin"]) as session:
                row = session.execute(
                    select(
                        AdminUserProject_admin.accessdb,
                        AdminUserProject_admin.id
                    ).filter_by(username=user_account)
                ).first()
            accessdb, src_user_id = row or ("", None)
            rows_userdb_list = accessdb.split("/") if accessdb else []

            answ_all_list_quotation = []
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(
                weeks=get_time_range_limit()
            )

            for alias in rows_userdb_list:
                if "dop" in query_string_dict:
                    if engine_nick[alias] != query_string_dict["dop"]:
                        continue

                eng_key = engine_nick[alias]
                db_name = engine_nick_name[alias]  # Get actual database name for cross-DB JOIN

                # Get synced usernames if non-manager
                is_manager = "manager" in user_account_status.split("/")
                allowed_names = []
                if not is_manager and matches_allowed_status(user_account_status, USERS_STATUS_LIST):
                    with Session(engine["DB_admin"]) as sync_sess:
                        synced_names = sync_sess.execute(
                            select(AccountSyncSetting.target_username)
                            .where(
                                AccountSyncSetting.db_name == alias,
                                AccountSyncSetting.source_user_id == src_user_id,
                                AccountSyncSetting.sync_enabled == True
                            )
                        ).scalars().all()
                    allowed_names = [user_account] + list(synced_names)

                with Session(engine[eng_key]) as session:
                    # Test if DB_admin is accessible from this database server
                    can_access_db_admin = True
                    try:
                        test_query = "SELECT 1 FROM [DB_admin].[dbo].[QuotationsStatus] WHERE 1=0"
                        session.execute(text(test_query))
                    except Exception:
                        can_access_db_admin = False
                        session.rollback()  # Fix session state after failed cross-DB query

                    # Build WHERE conditions dynamically
                    where_conditions = [
                        f"q.QuotationDate > '{cutoff.strftime('%Y-%m-%d %H:%M:%S')}'"
                    ]

                    # User permission filter
                    if allowed_names:
                        allowed_names_sql = "', '".join([name.replace("'", "''") for name in allowed_names])
                        where_conditions.append(
                            f"(e.FirstName IN ('{allowed_names_sql}') OR e.FirstName IS NULL)"
                        )

                    # Sales rep filter
                    if sales_rep_filters:
                        sales_rep_sql = "', '".join([name.replace("'", "''") for name in sales_rep_filters])
                        where_conditions.append(f"e.FirstName IN ('{sales_rep_sql}')")

                    # Search filter
                    if "search" in query_string_dict:
                        search_term = query_string_dict["search"].replace("'", "''")
                        if search_term:
                            where_conditions.append(
                                f"""(
                                    CAST(q.QuotationNumber AS VARCHAR) LIKE '%{search_term}%' OR
                                    q.BusinessName LIKE '%{search_term}%' OR
                                    q.AccountNo LIKE '%{search_term}%' OR
                                    q.AutoOrderNo LIKE '%{search_term}%' OR
                                    CAST(q.QuotationTotal AS VARCHAR) LIKE '%{search_term}%' OR
                                    e.FirstName LIKE '%{search_term}%'
                                )"""
                            )

                    # Status filter - applied before pagination
                    # For same-server: use SQL JOIN with CASE expression
                    # For cross-server: pre-fetch matching IDs from DB_admin
                    status_filtered_ids = None
                    has_status_error_filter = False
                    if status_filters:
                        status_sql = "', '".join([status.replace("'", "''") for status in status_filters])
                        if can_access_db_admin:
                            # Same server - use SQL JOIN approach
                            where_conditions.append(
                                f"""(CASE
                                    WHEN q.AutoOrderNo IS NOT NULL THEN 'Converted'
                                    ELSE COALESCE(qs.Status, 'Status Error')
                                END) IN ('{status_sql}')"""
                            )
                        else:
                            # Cross-server: Two-phase approach
                            has_converted = any(s.upper() == "CONVERTED" for s in status_filters)
                            has_status_error_filter = any(s.upper() == "STATUS ERROR" for s in status_filters)
                            # Get statuses that exist in DB_admin (exclude Converted and Status Error)
                            db_admin_statuses = [s for s in status_filters if s.upper() not in ("CONVERTED", "STATUS ERROR")]

                            # Pre-fetch IDs matching actual statuses from DB_admin
                            if db_admin_statuses:
                                status_filtered_ids = get_status_filtered_ids(cutoff, db_admin_statuses)

                            # Build WHERE condition
                            # Note: If "Status Error" is in filters, we can't pre-filter - those are quotations
                            # WITHOUT records in QuotationsStatus, so we'll filter post-query
                            if has_status_error_filter:
                                # When "Status Error" is requested, we can't pre-filter in SQL
                                # because those are quotations WITHOUT records in QuotationsStatus.
                                # We need to fetch all quotations and filter after enrichment.
                                # However, we can still pre-filter for Converted (AutoOrderNo IS NOT NULL)
                                # and known DB_admin statuses to optimize, but ONLY if "Status Error"
                                # is the ONLY filter. If combined with other statuses, we need all records.

                                # For simplicity, when "Status Error" is in filters, fetch all and filter post-query
                                pass  # No WHERE condition for status - post-query filtering will happen
                            else:
                                conditions = []
                                if has_converted:
                                    conditions.append("q.AutoOrderNo IS NOT NULL")
                                if db_admin_statuses and status_filtered_ids:
                                    ids_sql = "', '".join(str(qid) for qid in status_filtered_ids)
                                    conditions.append(f"CAST(q.QuotationID AS VARCHAR) IN ('{ids_sql}')")

                                if conditions:
                                    where_conditions.append(f"({' OR '.join(conditions)})")
                                elif db_admin_statuses and not status_filtered_ids:
                                    # No IDs match the status filter - skip this database
                                    continue

                    where_clause = " AND ".join(where_conditions)

                    # Order by
                    order_by_clause = "q.QuotationID DESC"
                    if order_by_list:
                        # Take the first sorting rule (DataTables usually sends one at a time)
                        col, direction = order_by_list[0].split(" ")
                        # Validate column name to prevent SQL injection
                        allowed_cols = ["QuotationID", "QuotationDate", "QuotationNumber", "AccountNo",
                                        "BusinessName", "AutoOrderNo", "Total", "ProfitMargin", "FirstName", "StatusQuotation"]
                        if col in allowed_cols:
                            # Map display column names to actual database column names
                            if col == "Total":
                                order_by_clause = f"q.QuotationTotal {direction.upper()}"
                            elif col == "ProfitMargin":
                                # ProfitMargin is a CASE expression, use the alias in ORDER BY
                                order_by_clause = f"ProfitMargin {direction.upper()}"
                            elif col == "FirstName":
                                order_by_clause = f"e.FirstName {direction.upper()}"
                            elif col == "StatusQuotation":
                                if can_access_db_admin:
                                    # Same server - can sort by StatusQuotation alias
                                    order_by_clause = f"StatusQuotation {direction.upper()}"
                                else:
                                    # Cross-server: Approximate sort - Converted first/last, others by QuotationID
                                    if direction.upper() == "ASC":
                                        order_by_clause = "CASE WHEN q.AutoOrderNo IS NOT NULL THEN 1 ELSE 0 END, q.QuotationID"
                                    else:
                                        order_by_clause = "CASE WHEN q.AutoOrderNo IS NOT NULL THEN 0 ELSE 1 END, q.QuotationID DESC"
                            else:
                                order_by_clause = f"q.{col} {direction.upper()}"

                    # Build raw SQL query with optional cross-database JOIN
                    if can_access_db_admin:
                        query_sql = f"""
                        SELECT
                            q.QuotationID,
                            q.QuotationDate,
                            q.QuotationNumber,
                            q.AccountNo,
                            q.BusinessName,
                            q.AutoOrderNo,
                            q.QuotationTotal AS Total,
                            CASE
                                WHEN qd_agg.TotalCost IS NULL OR qd_agg.TotalCost = 0 THEN 0
                                WHEN qd_agg.TotalPrice IS NULL THEN 0
                                ELSE ROUND(((qd_agg.TotalPrice / qd_agg.TotalCost) - 1) * 100, 2)
                            END AS ProfitMargin,
                            e.FirstName,
                            DB_NAME() AS DBname,
                            CASE
                                WHEN q.AutoOrderNo IS NOT NULL THEN 'Converted'
                                ELSE COALESCE(qs.Status, 'Status Error')
                            END AS StatusQuotation
                        FROM [{db_name}].[dbo].[Quotations_tbl] q
                        LEFT JOIN [{db_name}].[dbo].[Employees_tbl] e
                            ON q.SalesRepID = e.EmployeeID
                        LEFT JOIN [DB_admin].[dbo].[QuotationsStatus] qs
                            ON q.QuotationID = qs.Dop1
                        LEFT JOIN (
                            SELECT
                                QuotationID,
                                SUM(UnitCost * Qty) AS TotalCost,
                                SUM(UnitPrice * Qty) AS TotalPrice
                            FROM [{db_name}].[dbo].[QuotationsDetails_tbl]
                            GROUP BY QuotationID
                        ) qd_agg ON q.QuotationID = qd_agg.QuotationID
                        WHERE {where_clause}
                        ORDER BY {order_by_clause}
                        """

                        count_query = f"""
                        SELECT COUNT(*) AS total
                        FROM [{db_name}].[dbo].[Quotations_tbl] q
                        LEFT JOIN [{db_name}].[dbo].[Employees_tbl] e
                            ON q.SalesRepID = e.EmployeeID
                        LEFT JOIN [DB_admin].[dbo].[QuotationsStatus] qs
                            ON q.QuotationID = qs.Dop1
                        WHERE {where_clause}
                        """
                    else:
                        # Fallback query without DB_admin access - status will be enriched later
                        query_sql = f"""
                        SELECT
                            q.QuotationID,
                            q.QuotationDate,
                            q.QuotationNumber,
                            q.AccountNo,
                            q.BusinessName,
                            q.AutoOrderNo,
                            q.QuotationTotal AS Total,
                            CASE
                                WHEN qd_agg.TotalCost IS NULL OR qd_agg.TotalCost = 0 THEN 0
                                WHEN qd_agg.TotalPrice IS NULL THEN 0
                                ELSE ROUND(((qd_agg.TotalPrice / qd_agg.TotalCost) - 1) * 100, 2)
                            END AS ProfitMargin,
                            e.FirstName,
                            DB_NAME() AS DBname,
                            CASE
                                WHEN q.AutoOrderNo IS NOT NULL THEN 'Converted'
                                ELSE NULL
                            END AS StatusQuotation
                        FROM [{db_name}].[dbo].[Quotations_tbl] q
                        LEFT JOIN [{db_name}].[dbo].[Employees_tbl] e
                            ON q.SalesRepID = e.EmployeeID
                        LEFT JOIN (
                            SELECT
                                QuotationID,
                                SUM(UnitCost * Qty) AS TotalCost,
                                SUM(UnitPrice * Qty) AS TotalPrice
                            FROM [{db_name}].[dbo].[QuotationsDetails_tbl]
                            GROUP BY QuotationID
                        ) qd_agg ON q.QuotationID = qd_agg.QuotationID
                        WHERE {where_clause}
                        ORDER BY {order_by_clause}
                        """

                        count_query = f"""
                        SELECT COUNT(*) AS total
                        FROM [{db_name}].[dbo].[Quotations_tbl] q
                        LEFT JOIN [{db_name}].[dbo].[Employees_tbl] e
                            ON q.SalesRepID = e.EmployeeID
                        WHERE {where_clause}
                        """

                    # Get total count for pagination (before OFFSET/FETCH)
                    total_count = session.execute(text(count_query)).scalar()

                    # Store total in request state
                    if not hasattr(request.state, 'quotations_total_count'):
                        request.state.quotations_total_count = 0
                    request.state.quotations_total_count += total_count

                    # Get unique sales reps for dropdown (only once)
                    if not hasattr(request.state, 'unique_sales_reps'):
                        unique_reps_query = f"""
                        SELECT DISTINCT e.FirstName
                        FROM [{db_name}].[dbo].[Quotations_tbl] q
                        INNER JOIN [{db_name}].[dbo].[Employees_tbl] e
                            ON q.SalesRepID = e.EmployeeID
                        WHERE q.QuotationDate > '{cutoff.strftime('%Y-%m-%d %H:%M:%S')}'
                            AND e.FirstName IS NOT NULL
                        ORDER BY e.FirstName
                        """
                        unique_reps = session.execute(text(unique_reps_query)).scalars().all()
                        request.state.unique_sales_reps = sorted(list(unique_reps))

                    # Apply pagination (SQL Server 2012+ syntax)
                    query_sql_paginated = f"""
                    {query_sql.strip()}
                    OFFSET {skip} ROWS
                    FETCH NEXT {limit} ROWS ONLY
                    """

                    answ_all_list_quotation_temp = (
                        session.execute(text(query_sql_paginated)).mappings().all()
                    )

                    # ENRICHMENT: Batch lookup status for cross-server databases
                    if not can_access_db_admin and answ_all_list_quotation_temp:
                        # Convert to mutable dicts
                        results_list = [dict(row) for row in answ_all_list_quotation_temp]

                        # Get IDs needing status lookup (those with NULL status)
                        ids_needing_status = [
                            str(row['QuotationID'])
                            for row in results_list
                            if row.get('StatusQuotation') is None
                        ]

                        if ids_needing_status:
                            try:
                                status_map = batch_lookup_status(ids_needing_status)
                                for row in results_list:
                                    if row.get('StatusQuotation') is None:
                                        qid = str(row['QuotationID'])
                                        row['StatusQuotation'] = status_map.get(qid, 'Status Error')
                            except Exception as e:
                                print(f"⚠️ Status enrichment failed: {e}")
                                # Fallback: set Status Error for all records without status
                                for row in results_list:
                                    if row.get('StatusQuotation') is None:
                                        row['StatusQuotation'] = 'Status Error'

                        # POST-QUERY FILTERING: When "Status Error" is in filters,
                        # we fetched all records and need to filter after enrichment
                        if has_status_error_filter and status_filters:
                            # Filter to only include records matching the status filters
                            filtered_results = []
                            status_filters_upper = [s.upper() for s in status_filters]
                            for row in results_list:
                                row_status = (row.get('StatusQuotation') or '').upper()
                                if row_status in status_filters_upper:
                                    filtered_results.append(row)
                            results_list = filtered_results

                        answ_all_list_quotation.extend(results_list)
                    else:
                        answ_all_list_quotation.extend(answ_all_list_quotation_temp)

            return answ_all_list_quotation

        elif active_table == "quotationsdetails1_tbl":
            list_obj_detail: list[str] = list()
            dict_obj: dict[str:str] = dict()
            DB_send = engine_nick[query_url["DBname"]]
            with Session(engine[DB_send]) as session:
                stmt_quotation_edit_det = select(
                    QuotationsDetails_tbl.__table__.columns,
                    func.db_name().label("DBname"),
                ).filter_by(QuotationID=query_url["QuotationID"].replace("'", ""))
                rows_quotation_edit_det = (
                    session.execute(stmt_quotation_edit_det).mappings().all()
                )
                for i in rows_quotation_edit_det:
                    dict_obj_detail: dict[str:str] = dict()
                    dict_obj_detail["LineID"] = i["LineID"]
                    dict_obj_detail["ProductDescription"] = i["ProductDescription"]
                    dict_obj_detail["ProductSKU"] = i["ProductSKU"]
                    dict_obj_detail["Qty"] = i["Qty"]
                    dict_obj_detail["UnitPrice"] = f'${round(i["UnitPrice"], 2)}'
                    list_obj_detail.append(dict_obj_detail)
            return rows_quotation_edit_det

        elif active_table == "invoices2_tbl":
            handler = InvoiceHandler(
                request,
                user_account,
                user_account_status,
                engine,
                engine_nick,
            )

            return handler.find_all()

        elif active_table == "quotations3_tbl":
            list_obj_detail: list[str] = list()
            dict_obj: dict[str:str] = dict()
            DB_send = engine_nick[query_url["DBname"]]
            with Session(engine[DB_send]) as session:
                stmt_quotation_edit_det = (
                    select(
                        QuotationsDetails_tbl.__table__.columns,
                        func.db_name().label("DBname"),
                        func.round(
                            (
                                QuotationsDetails_tbl.Qty
                                * QuotationsDetails_tbl.UnitPrice
                            ),
                            2,
                        ).label("Total"),
                    )
                    .filter_by(QuotationID=query_url["QuotationID"].replace("'", ""))
                    .limit(limit)
                )
                rows_quotation_edit_det = (
                    session.execute(stmt_quotation_edit_det).mappings().all()
                )
                for i in rows_quotation_edit_det:
                    dict_obj_detail: dict[str:str] = dict()
                    Price = round(i["UnitPrice"])
                    QTY = i["Qty"]
                    dict_obj_detail["id"] = i["LineID"]
                    dict_obj_detail["SessionID"] = user_account
                    dict_obj_detail["SourceDB"] = i["LineID"]
                    dict_obj_detail["AccountNo"] = i["LineID"]
                    dict_obj_detail["BusinessName"] = i["LineID"]
                    dict_obj_detail["ProductDescription"] = i["ProductDescription"]
                    dict_obj_detail["SKU"] = i["ProductSKU"]
                    dict_obj_detail["QTY"] = i["Qty"]
                    dict_obj_detail["Price"] = f"${round(Price, 2)}"
                    dict_obj_detail["Total"] = Price * QTY
                    list_obj_detail.append(dict_obj_detail)
            return rows_quotation_edit_det

        elif active_table == "checkinvertory":
            list_empty_items: list[str] = list()
            list_obj_detail: list[str] = list()
            dict_obj: dict[str:str] = dict()
            with Session(engine["DB1"]) as session:
                stmt_checkinvertory = select(
                    Items_tbl.ProductUPC,
                    Items_tbl.ProductDescription,
                    Items_tbl.CateID,
                    Items_tbl.SubCateID,
                ).where(
                    and_(
                        Items_tbl.Discontinued == 0,
                        Items_tbl.ReorderLevel == 7,
                    )
                )
                rows_checkinvertory = (
                    session.execute(stmt_checkinvertory).mappings().all()
                )
            for i in engine_db_nick_name:
                if i == "DB1":
                    continue
                with Session(engine[i]) as session:
                    for count, i1 in enumerate(rows_checkinvertory):
                        ProductUPC = i1["ProductUPC"]
                        ProductDescription = i1["ProductDescription"]
                        CateID = i1["CateID"]
                        SubCateID = i1["SubCateID"]
                        dict_empty_items: dict[str:str] = dict()
                        stmt_checkinvertoryinbase = select(
                            Items_tbl.ProductUPC,
                        ).where(
                            and_(
                                Items_tbl.Discontinued == 0,
                                Items_tbl.ProductUPC == ProductUPC,
                            )
                        )

                        rows_checkinvertoryinbase = (
                            session.execute(stmt_checkinvertoryinbase).mappings().all()
                        )

                        if not rows_checkinvertoryinbase:
                            dict_empty_items.update({"CateID": CateID})
                            dict_empty_items.update({"SubCateID": SubCateID})
                            dict_empty_items.update({"ProductUPC": ProductUPC})
                            dict_empty_items.update(
                                {"ProductDescription": ProductDescription}
                            )
                            dict_empty_items.update({"DB": engine_db_nick_name[i]})
                            dict_empty_items.update({"Status": "missing"})
                            list_empty_items.append(dict_empty_items)
            return []
        if isinstance(session, AsyncSession):
            return (await session.execute(text(stmt))).scalars().unique().all()
        return (
            (await anyio.to_thread.run_sync(session.execute, stmt))
            .scalars()
            .unique()
            .all()
        )

    async def find_all1(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        if other == "categories_db1":
            engine_for_query = engine["DB1"]
        elif other == "categories_db2":
            engine_for_query = engine["DB2"]
        elif other == "categories_db3":
            engine_for_query = engine["DB3"]
        elif other == "categories_db4":
            engine_for_query = engine["DB4"]
        session = session_init(request)
        stmt = self.get_list_query().offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        order_by = []
        stmt_str = (
            str(stmt).split(" ")[1].split(".")[1].replace('"', "").replace(",", "")
            + " asc"
        )
        order_by.append(stmt_str)

        stmt = stmt.order_by(*build_order_clauses(order_by, self.model))

        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))
        active_table = request.path_params["identity"]
        query = "select Categories_tbl.CategoryName, SubCategories_tbl.CategoryID,SubCategories_tbl.SubCateID, SubCategories_tbl.SubCateName from SubCategories_tbl \
		inner join Categories_tbl on SubCategories_tbl.CategoryID = Categories_tbl.CategoryID Where CategoryName <> 'POS BUTTONS'\
		Order by Categories_tbl.CategoryName Asc"
        find_cat = f"'%{where}%'"
        if "where" in request._query_params:
            where = str(request._query_params).split("=")[-1]
        elif "pks" in request._query_params:
            if str(request._query_params).count("pks") > 1:
                where = urllib.parse.unquote_plus(
                    ",".join(str(request._query_params).split("&pks=")[1:])
                )
            else:
                where = urllib.parse.unquote_plus(
                    str(request._query_params).split("=")[-1]
                )
            find_cat = f"'{where}'"
        if where is not None:
            query = f"select Categories_tbl.CategoryName, SubCategories_tbl.CategoryID,SubCategories_tbl.SubCateID, SubCategories_tbl.SubCateName from SubCategories_tbl \
			inner join Categories_tbl on SubCategories_tbl.CategoryID = Categories_tbl.CategoryID Where CategoryName <> 'POS BUTTONS' \
			and lower(SubCategories_tbl.SubCateName) LIKE lower({find_cat}) \
			Order by Categories_tbl.CategoryName Asc"
        query_answer = query_f(engine_for_query, query)
        return query_answer

    async def find_all_manutest(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        if other == "manutest1":
            engine_for_query = engine["DB1"]
        elif other == "manutest2":
            engine_for_query = engine["DB2"]
        elif other == "manutest3":
            engine_for_query = engine["DB3"]
        elif other == "manutest4":
            engine_for_query = engine["DB4"]

        session = session_init(request)
        stmt = self.get_list_query().offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        order_by = []
        stmt_str = (
            str(stmt).split(" ")[1].split(".")[1].replace('"', "").replace(",", "")
            + " asc"
        )
        order_by.append(stmt_str)
        stmt = stmt.order_by(*build_order_clauses(order_by, self.model))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))

        active_table = request.path_params["identity"]
        query = "select * from Manufacturers_tbl"
        if "where" in request._query_params:
            where = str(request._query_params).split("=")[-1]
        elif "pks" in request._query_params:
            where = urllib.parse.unquote_plus(str(request._query_params).split("=")[-1])
        if where is not None:
            query = f"select * from Manufacturers_tbl Where lower(Manufacturers_tbl.ManuName) LIKE lower('%{where}%')"
        query_answer = query_f(engine_for_query, query)
        return query_answer

    async def find_all_unitid(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        if other == "unitid1":
            engine_for_query = engine["DB1"]
        elif other == "unitid2":
            engine_for_query = engine["DB2"]
        elif other == "unitid3":
            engine_for_query = engine["DB3"]
        elif other == "unitid4":
            engine_for_query = engine["DB4"]
        session = session_init(request)
        stmt = self.get_list_query().offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        order_by = []
        stmt_str = (
            str(stmt).split(" ")[1].split(".")[1].replace('"', "").replace(",", "")
            + " asc"
        )
        order_by.append(stmt_str)
        stmt = stmt.order_by(*build_order_clauses(order_by, self.model))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))

        active_table = request.path_params["identity"]
        query = "select * from Units_tbl"
        if "where" in request._query_params:
            where = str(request._query_params).split("=")[-1]
        elif "pks" in request._query_params:
            where = urllib.parse.unquote_plus(str(request._query_params).split("=")[-1])
        if where is not None:
            query = f"select * from Units_tbl Where lower(Units_tbl.UnitDesc) LIKE lower('%{where}%')"

        query_answer = query_f(engine_for_query, query)
        return query_answer

    async def find_all_tax(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        if other == "taxid1":
            engine_for_query = engine["DB1"]
        elif other == "taxid2":
            engine_for_query = engine["DB2"]
        elif other == "taxid3":
            engine_for_query = engine["DB3"]
        elif other == "taxid4":
            engine_for_query = engine["DB4"]
        session = session_init(request)
        stmt = self.get_list_query().offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        order_by = []
        stmt_str = (
            str(stmt).split(" ")[1].split(".")[1].replace('"', "").replace(",", "")
            + " asc"
        )
        order_by.append(stmt_str)

        stmt = stmt.order_by(*build_order_clauses(order_by, self.model))

        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))

        active_table = request.path_params["identity"]
        query = "select * from ItemTaxes_tbl"
        if "where" in request._query_params:
            where = str(request._query_params).split("=")[-1]
        elif "pks" in request._query_params:
            where = urllib.parse.unquote_plus(str(request._query_params).split("=")[-1])
        if where is not None:
            query = f"select * from ItemTaxes_tbl Where lower(ItemTaxes_tbl.TaxName) LIKE lower('%{where}%')"
        query_answer = query_f(engine_for_query, query)
        return query_answer

    async def find_all_queryalias1(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        engine_for_query = engine["DB_admin"]
        session = session_init(request)
        stmt = self.get_list_query().offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        order_by = []
        stmt_str = (
            str(stmt).split(" ")[1].split(".")[1].replace('"', "").replace(",", "")
            + " asc"
        )
        order_by.append(stmt_str)
        stmt = stmt.order_by(*build_order_clauses(order_by, self.model))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))
        active_table = request.path_params["identity"]
        query = "select * from admin_query"
        pks_flag = 0
        if "where" in request._query_params:
            where = urllib.parse.unquote_plus(str(request._query_params).split("=")[-1])
            if where is not None:
                where = where.replace("'", "''")
                query = f"select * from admin_query Where lower(admin_query.alias) LIKE lower('{where}')"
        elif "pks" in request._query_params:
            where = urllib.parse.unquote_plus(str(request._query_params).split("=")[-1])
            pks_flag = 1
            if where is not None:
                where = where.replace("'", "''")
                query = f"select * from admin_query Where lower(admin_query.alias) LIKE lower('%{where}%')"
        query_answer = query_f(engine_for_query, query)
        if pks_flag == 1:
            return query_answer[:1]
        elif pks_flag == 0 and len(query_answer) < 2:
            query_answer_temp = ("", "")
            query_answer.append(query_answer_temp)
            return query_answer
        return query_answer

    async def find_all_quotation(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        engine_for_query = engine["DB_admin"]
        session = session_init(request)
        stmt = self.get_list_query().offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        order_by = []
        stmt_str = (
            str(stmt).split(" ")[1].split(".")[1].replace('"', "").replace(",", "")
            + " asc"
        )
        order_by.append(stmt_str)
        stmt = stmt.order_by(*build_order_clauses(order_by, self.model))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))
        active_table = request.path_params["identity"]
        query = "select * from admin_query"
        if "where" in request._query_params:
            where = str(request._query_params).split("=")[-1]
        elif "pks" in request._query_params:
            where = urllib.parse.unquote_plus(str(request._query_params).split("=")[-1])
        if where is not None:
            query = f"select * from admin_query Where lower(admin_query.alias) LIKE lower('%{where}%')"
        query_answer = query_f(engine_for_query, query)
        return query_answer

    async def find_all_prodtempl(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = " ",
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        if other == "prodtempldb1":
            engine_for_query = engine["DB1"]
        elif other == "prodtempldb2":
            engine_for_query = engine["DB2"]
        elif other == "prodtempldb3":
            engine_for_query = engine["DB3"]
        elif other == "prodtempldb4":
            engine_for_query = engine["DB4"]
        session = session_init(request)
        stmt = self.get_list_query().offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        order_by = []
        stmt_str = (
            str(stmt).split(" ")[1].split(".")[1].replace('"', "").replace(",", "")
            + " asc"
        )
        order_by.append(stmt_str)
        stmt = stmt.order_by(*build_order_clauses(order_by, self.model))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))

        active_table = request.path_params["identity"]
        pks_flag = 0
        query = "select ProductID,ProductDescription from Items_tbl Where Discontinued = 0"
        if "where" in request._query_params:
            where = urllib.parse.unquote_plus(str(request._query_params).split("=")[-1])
            if where is not None:
                if len(where) >= 3:
                    where = where.replace("'", "''")
                    query = f"select ProductID,ProductDescription from Items_tbl Where lower(ProductDescription) LIKE lower('%{where}%') and Discontinued = 0"
        elif "pks" in request._query_params:
            where = urllib.parse.unquote_plus(
                ",".join(str(request._query_params).split("&pks=")[1:])
            )
            pks_flag = 1
            if where is not None:
                if len(where) >= 3:
                    where = where.replace("'", "''")
                    query = f"select ProductID,ProductDescription from Items_tbl Where lower(ProductDescription) LIKE lower('%{where}') and Discontinued = 0"
        query_answer = query_f(engine_for_query, query)
        if pks_flag == 1:
            return query_answer[:1]
        elif pks_flag == 0 and len(query_answer) < 2:
            query_answer_temp = ("", "")
            query_answer.append(query_answer_temp)
            return query_answer
        else:
            return query_answer

    async def find_all_choicedb_source(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = " ",
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        user_account = request.state.user["name"].strip().lower()
        with Session(engine["DB_admin"]) as session:
            query = select(AdminDBs_admin.__table__.columns)
            query1 = select(AdminUserProject_admin.__table__.columns).filter_by(
                username=user_account
            )
            rows_quotation_status = session.execute(query1).mappings().all()
            query_answer0 = rows_quotation_status[0]["accessdb"].split("/")
            pks_flag = 0
            if "where" in request._query_params:
                where = urllib.parse.unquote_plus(
                    str(request._query_params).split("=")[-1]
                )
                if where is not None:
                    where = where.replace("'", "''")
                    query = select(AdminDBs_admin.__table__.columns).filter(
                        AdminDBs_admin.Nick.like(f"%{where}%")
                    )
            elif "pks" in request._query_params:
                where = urllib.parse.unquote_plus(
                    str(request._query_params).split("=")[-1]
                )
                pks_flag = 1
                if where is not None:
                    where = where.replace("'", "''")
                    query = select(AdminDBs_admin.__table__.columns).filter(
                        AdminDBs_admin.Nick.like(f"{where}")
                    )
            query_answer = session.execute(query).mappings().all()
            query_answer1 = list()
            for i in query_answer:
                if i["Nick"] in query_answer0:
                    query_answer1.append(i)
            return query_answer1

    async def find_all_businessnamequotation(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        dict_obj: Optional[List[str]] = None,
        model: Any = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:

        with Session(engine[engine_nick[db_form]]) as session:
            query = select(Customers_tbl.__table__.columns)
            query_answer = session.execute(query).mappings().all()
            pks_flag = 0
            req_query = str(request._query_params)
            if "where" in req_query:
                where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                if where is not None:
                    if len(where) >= 2:
                        query = select(Customers_tbl.__table__.columns).filter(
                            Customers_tbl.BusinessName.like(f"%{where}%")
                        )
            elif "pks" in req_query:
                if req_query.count("pks=") > 1:
                    req_query_temp = list()
                    req_query_split = req_query.split("&")
                    for i in req_query_split:
                        if i.split("=")[0] == "pks":
                            req_query_temp.append(
                                "".join(urllib.parse.unquote_plus(i).split("=")[1:])
                            )
                    where = ",".join(req_query_temp).replace("+", " ")
                else:
                    where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                pks_flag = 1
                if where is not None:
                    query = select(Customers_tbl.__table__.columns).filter(
                        Customers_tbl.BusinessName.like(f"{where}")
                    )
            query_answer = session.execute(query).mappings().all()
            if "pks" in req_query and len(query_answer) > 1:
                query_answer = query_answer[:1]
            return query_answer

    async def find_all_productdescriptionquotation(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        dict_obj: Optional[List[str]] = None,
        model: Any = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:
        with Session(engine[engine_nick[db_form]]) as session:
            pks_flag = 0
            req_query = str(request._query_params)
            if "where" in req_query:
                where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                if where is not None:
                    if len(where) >= 2:
                        query = select(Items_tbl.__table__.columns).filter(
                            Items_tbl.Discontinued == 0,
                            Items_tbl.ProductDescription.like(f"%{where}%"),
                        )
            elif "pks" in req_query:
                if req_query.count("pks=") > 1:
                    req_query_temp = list()
                    req_query_split = req_query.split("&")
                    for i in req_query_split:
                        if i.split("=")[0] == "pks":
                            req_query_temp.append(
                                "".join(urllib.parse.unquote_plus(i).split("=")[1:])
                            )
                    where = ",".join(req_query_temp).replace("+", " ")
                else:
                    where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                pks_flag = 1
                if where is not None:
                    query = select(Items_tbl.__table__.columns).filter(
                        Items_tbl.Discontinued == 0,
                        Items_tbl.ProductDescription.like(f"{where}"),
                    )
            query_answer = session.execute(query).mappings().all()
            if "pks" in req_query and len(query_answer) > 1:
                query_answer = query_answer[:1]
            return query_answer

    async def find_all_productdescriptionquotationedit(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        dict_obj: Optional[List[str]] = None,
        model: Any = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:
        with Session(engine[engine_nick[db_form]]) as session:
            pks_flag = 0
            req_query = str(request._query_params)
            if "where" in req_query:
                where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                if where is not None:
                    if len(where) >= 2:
                        query = select(Items_tbl.__table__.columns).filter(
                            Items_tbl.Discontinued == 0,
                            Items_tbl.ProductDescription.like(f"%{where}%"),
                        )
            elif "pks" in req_query:
                if req_query.count("pks=") > 1:
                    req_query_temp = list()
                    req_query_split = req_query.split("&")
                    for i in req_query_split:
                        if i.split("=")[0] == "pks":
                            req_query_temp.append(
                                "".join(urllib.parse.unquote_plus(i).split("=")[1:])
                            )
                    where = ",".join(req_query_temp).replace("+", " ")
                else:
                    where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                pks_flag = 1
                if where is not None:
                    query = select(Items_tbl.__table__.columns).filter(
                        Items_tbl.Discontinued == 0,
                        Items_tbl.ProductDescription.like(f"{where}"),
                    )
            query_answer = session.execute(query).mappings().all()
            if "pks" in req_query and len(query_answer) > 1:
                query_answer = query_answer[:1]
            return query_answer

    async def find_all_productskuquotation(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        dict_obj: Optional[List[str]] = None,
        model: Any = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:
        with Session(engine[engine_nick[db_form]]) as session:
            pks_flag = 0
            if "where" in request._query_params:
                where = urllib.parse.unquote_plus(
                    str(request._query_params).split("=")[-1]
                )
                if where is not None:
                    if len(where) >= 2:
                        query = select(Items_tbl.__table__.columns).filter(
                            Items_tbl.Discontinued == 0,
                            Items_tbl.ProductSKU.like(f"%{where}%"),
                        )
            elif "pks" in request._query_params:
                where = urllib.parse.unquote_plus(
                    str(request._query_params).split("=")[-1]
                )
                pks_flag = 1
                if where is not None:
                    query = select(Items_tbl.__table__.columns).filter(
                        Items_tbl.Discontinued == 0,
                        Items_tbl.ProductSKU.like(f"{where}"),
                    )
            query_answer = session.execute(query).mappings().all()
            return query_answer

    async def find_all_accountnoquotation(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:
        with Session(engine[engine_nick[db_form]]) as session:
            query = select(Customers_tbl.__table__.columns)
            query_answer = session.execute(query).mappings().all()
            pks_flag = 0
            if "where" in request._query_params:
                where = urllib.parse.unquote_plus(
                    str(request._query_params).split("=")[-1]
                )
                if where is not None:
                    if len(where) >= 2:
                        query = select(Customers_tbl.__table__.columns).filter(
                            Customers_tbl.AccountNo.like(f"%{where}%")
                        )
            elif "pks" in request._query_params:
                where = urllib.parse.unquote_plus(
                    str(request._query_params).split("=")[-1]
                )
                pks_flag = 1
                if where is not None:
                    query = select(Customers_tbl.__table__.columns).filter(
                        Customers_tbl.AccountNo.like(f"{where}")
                    )
            query_answer = session.execute(query).mappings().all()
            return query_answer

    async def find_all_productdescriptionmanual(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        dict_obj: Optional[List[str]] = None,
        model: Any = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:
        with Session(engine["DB1"]) as session:
            pks_flag = 0
            req_query = str(request._query_params)
            if "where" in req_query:
                where = urllib.parse.unquote_plus(
                    str(request._query_params).split("=")[-1]
                )
                if where is not None:
                    if len(where) >= 2:
                        query = select(Items_tbl.__table__.columns).filter(
                            Items_tbl.Discontinued == 0,
                            Items_tbl.ProductDescription.like(f"%{where}%"),
                        )
            elif "pks" in request._query_params:
                if req_query.count("pks=") > 1:
                    req_query_temp = list()
                    req_query_split = req_query.split("&")
                    for i in req_query_split:
                        if i.split("=")[0] == "pks":
                            req_query_temp.append(
                                "".join(urllib.parse.unquote_plus(i).split("=")[1:])
                            )
                    where = ",".join(req_query_temp).replace("+", " ")
                else:
                    where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                pks_flag = 1
                if where is not None:
                    query = select(Items_tbl.__table__.columns).filter(
                        Items_tbl.Discontinued == 0,
                        Items_tbl.ProductDescription.like(f"{where}"),
                    )

            query_answer = session.execute(query).mappings().all()
            return query_answer

    async def find_all_productskumanual(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        dict_obj: Optional[List[str]] = None,
        model: Any = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:
        with Session(engine["DB1"]) as session:
            pks_flag = 0
            req_query = str(request._query_params)
            if "where" in req_query:
                where = urllib.parse.unquote_plus(
                    str(request._query_params).split("=")[-1]
                )
                if where is not None:
                    if len(where) >= 2:
                        query = select(Items_tbl.__table__.columns).filter(
                            Items_tbl.Discontinued == 0,
                            Items_tbl.ProductSKU.like(f"%{where}%"),
                        )
            elif "pks" in request._query_params:
                if req_query.count("pks=") > 1:
                    req_query_temp = list()
                    req_query_split = req_query.split("&")
                    for i in req_query_split:
                        if i.split("=")[0] == "pks":
                            req_query_temp.append(
                                "".join(urllib.parse.unquote_plus(i).split("=")[1:])
                            )
                    where = ",".join(req_query_temp).replace("+", " ")
                else:
                    where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                pks_flag = 1
                if where is not None:
                    query = select(Items_tbl.__table__.columns).filter(
                        Items_tbl.Discontinued == 0,
                        Items_tbl.ProductSKU.like(f"{where}"),
                    )
            query_answer = session.execute(query).mappings().all()
            return query_answer

    async def find_all_choicedbdestination(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        dict_obj: Optional[List[str]] = None,
        model: Any = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:
        with Session(engine["DB_admin"]) as session:
            stmt_quotation_db = select(AdminDBs_admin.__table__.columns)
            query_answer = session.execute(stmt_quotation_db).mappings().all()
            return query_answer

    async def find_all_accountnumbercopy(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        dict_obj: Optional[List[str]] = None,
        model: Any = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:
        with Session(engine[engine_nick[db_form]]) as session:
            pks_flag = 0
            req_query = str(request._query_params)
            if "where" in req_query:
                where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                if where is not None:
                    if len(where) >= 0:
                        query = select(Customers_tbl.__table__.columns).filter(
                            Customers_tbl.AccountNo.like(f"%{where}%"),
                        )
            elif "pks" in req_query:
                if req_query.count("pks=") > 1:
                    req_query_temp = list()
                    req_query_split = req_query.split("&")

                    for i in req_query_split:
                        if i.split("=")[0] == "pks":
                            req_query_temp.append(
                                "".join(urllib.parse.unquote_plus(i).split("=")[1:])
                            )
                    where = ",".join(req_query_temp).replace("+", " ")
                else:
                    where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                pks_flag = 1
                if where is not None:
                    query = select(Customers_tbl.__table__.columns).filter(
                        Customers_tbl.AccountNo.like(f"{where}"),
                    )
            query_answer = session.execute(query).mappings().all()
            if "pks" in req_query and len(query_answer) > 1:
                query_answer = query_answer[:1]
            return query_answer

    async def find_all_salesrepinvoices(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        other: Optional[List[str]] = None,
        dict_obj: Optional[List[str]] = None,
        model: Any = None,
        db_form: Optional[str] = None,
    ) -> Sequence[Any]:
        with Session(engine[engine_nick[db_form]]) as session:
            pks_flag = 0
            req_query = str(request._query_params)
            if "where" in req_query:
                where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                if where is not None:
                    if len(where) >= 0:
                        query = select(Employees_tbl.__table__.columns).filter(
                            Employees_tbl.FirstName.like(f"%{where}%"),
                        )
            elif "pks" in req_query:
                if req_query.count("pks=") > 1:
                    req_query_temp = list()
                    req_query_split = req_query.split("&")

                    for i in req_query_split:
                        if i.split("=")[0] == "pks":
                            req_query_temp.append(
                                "".join(urllib.parse.unquote_plus(i).split("=")[1:])
                            )
                    where = ",".join(req_query_temp).replace("+", " ")
                else:
                    where = urllib.parse.unquote_plus(req_query.split("=")[-1])
                pks_flag = 1
                if where is not None:
                    query = select(Employees_tbl.__table__.columns).filter(
                        Employees_tbl.FirstName.like(f"{where}")
                    )
            query_answer = session.execute(query).mappings().all()
            if "pks" in req_query and len(query_answer) > 1:
                query_answer = query_answer[:1]
            return query_answer

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        session = session_init(request)
        stmt = select(self.model).where(self._pk_column == self._pk_coerce(pk))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalars().unique().one_or_none()
        return (
            (await anyio.to_thread.run_sync(session.execute, stmt))
            .scalars()
            .unique()
            .one_or_none()
        )

    async def find_by_pks(self, request: Request, pks: List[Any]) -> Sequence[Any]:
        session = session_init(request)
        stmt = select(self.model).where(self._pk_column.in_(map(self._pk_coerce, pks)))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalars().unique().all()
        return (
            (await anyio.to_thread.run_sync(session.execute, stmt))
            .scalars()
            .unique()
            .all()
        )

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        pass

    async def validate_load_query(self, request: Request, data: Dict[str, Any]) -> None:
        pass

    async def validate_save_query(self, request: Request, data: Dict[str, Any]) -> None:
        pass

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data)
            await self.validate(request, data)
            session = session_init(request)

            obj = await self._populate_obj(request, self.model(), data)
            session.add(obj)
            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                await anyio.to_thread.run_sync(session.commit)
                await anyio.to_thread.run_sync(session.refresh, obj)
            return obj
        except Exception as e:
            return self.handle_exception(e)

    async def create_load_query(self, request: Request, data: Dict[str, Any]) -> Any:

        try:
            data = await self._arrange_data(request, data)
            await self.validate_load_query(request, data)

        except Exception as e:
            return self.handle_exception(e)

    async def create_save_query(self, request: Request, data: Dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data)
            await self.validate_save_query(request, data)

        except Exception as e:
            return self.handle_exception(e)

    async def create_reserve_quotation(
        self, request: Request, data: Dict[str, Any]
    ) -> Any:
        try:
            data = await self._arrange_data(request, data)
            await self.validate_reserve_quotation(request, data)

        except Exception as e:
            return self.handle_exception(e)

    async def add_items_quotation(self, request: Request, data: Dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data)
            await self.validate_new_quotation(request, data)

        except Exception as e:
            return self.handle_exception(e)

    async def create1(self, request: Request, data: Dict[str, Any]) -> Any:
        identity_req = request.path_params["identity"]
        try:
            data = await self._arrange_data(request, data)
            await self.validate(request, data)

        except Exception as e:
            return self.handle_exception(e)

        if identity_req == "items_tbl":

            data_sku = data["ProductSKU"]
            gen_list = gen_name()

            if len(data_sku) >= 14:
                query_sku = f"select * from Items_tbl Where lower(Items_tbl.ProductSKU) LIKE lower('{data_sku.lower()[:14]}%')"
            else:
                query_sku = f"select * from Items_tbl Where lower(Items_tbl.ProductSKU) LIKE lower('{data_sku.lower()}')"

            answ_sku_list: List[str] = list()
            with Session(engine["DB1"]) as session:
                answ1 = session.execute(text(query_sku)).all()
                if answ1:
                    answ_sku_list.append(gen_list[0])
            with Session(engine["DB2"]) as session:
                answ2 = session.execute(text(query_sku)).all()
                if answ2:
                    answ_sku_list.append(gen_list[1])

            with Session(engine["DB3"]) as session:
                answ3 = session.execute(text(query_sku)).all()
                if answ3:
                    answ_sku_list.append(gen_list[2])
            
            with Session(engine["DB4"]) as session:
                answ4 = session.execute(text(query_sku)).all()
                if answ4:
                    answ_sku_list.append(gen_list[SCW_INDEX])

            if answ_sku_list and len(answ_sku_list) == ACTIVE_DB_COUNT:
                return "yes", answ_sku_list
            [
                data.update(
                    {i: f"{datetime.datetime.today().strftime('%Y-%m-%d')} 00:00:00"}
                )
                for i in column_list_date
            ]
            [data.update({i: ""}) for i in column_list_str]
            [data.update({i: 0}) for i in column_list_zero]
            [data.update({i: 1}) for i in column_list_one]
            ProductSKU = data["ProductSKU"]
            if data["UnitCost2"]:
                UnitCost2 = float(data["UnitCost2"])
            else:
                UnitCost2 = 0
            query_db1 = "INSERT INTO [Items_tbl] ([CateID], [ManuID], [UnitCost], [UnitPrice], [SubCateID], [UnitID], [ItemTaxID], "
            query_db2 = "INSERT INTO [Items_tbl] ([CateID], [ManuID], [UnitCost], [UnitPrice], [SubCateID], [UnitID], [ItemTaxID], "
            query_db3 = "INSERT INTO [Items_tbl] ([CateID], [ManuID], [UnitCost], [UnitPrice], [SubCateID], [UnitID], [ItemTaxID], "
            query_db4 = "INSERT INTO [Items_tbl] ([CateID], [ManuID], [UnitCost], [UnitPrice], [SubCateID], [UnitID], [ItemTaxID], "
            if data:
                # When form field names include DB index suffixes (e.g. UnitCost4)
                # the real table column is usually the base name (UnitCost).
                # Strip trailing digits from field names when building the
                # column list and avoid appending duplicate columns.
                import re

                suf_re = re.compile(r"(\d+)$")
                existing = set(re.findall(r"\[([^\]]+)\]", query_db1))
                # Map some form field bases to actual table column names
                alias_map = {
                    "TaxID": "ItemTaxID",
                    "UnitQty": "CountInUnit",
                    "ManuName": "ManuID",
                    "CategoryName": "CateID",
                    "SubCateName": "SubCateID",
                    "UnitDesc": "UnitID",
                    "Qty": "QuantOnHand",
                    # add more mappings here if needed in future
                }
                appended_keys = []  # list of (form_key, column_name)
                for key in data:
                    if key in miss_list or key in cate_dif_db:
                        continue
                    base = suf_re.sub("", key)
                    col = alias_map.get(base, base)
                    if col not in existing:
                        query_db1 = f"{query_db1}[{col}], "
                        query_db2 = f"{query_db2}[{col}], "
                        query_db3 = f"{query_db3}[{col}], "
                        query_db4 = f"{query_db4}[{col}], "
                        existing.add(col)
                        appended_keys.append((key, col))
            query_temp = ") OUTPUT inserted.[ProductID] VALUES ("
            query_db1 = (
                query_db1
                + query_temp
                + f"{no_null_categ(data['CateID1'])[0]}, "
                + f"{no_null_manuid(data['ManuID1'])}, "
                + f"{no_null_manuid(data['UnitCost1'])}, "
                + f"{no_null_manuid(data['UnitPrice11'])}, "
                + f"{no_null_categ(data['CateID1'])[1]}, "
                + f"{no_null_manuid(data['UnitID11'])}, "
                + f"{no_null_manuid(data['TaxID11'])}, "
            )
            query_db2 = (
                query_db2
                + query_temp
                + f"{no_null_categ(data['CateID2'])[0]}, "
                + f"{no_null_manuid(data['ManuID2'])}, "
                + f"{no_null_manuid(data['UnitCost2'])}, "
                + f"{no_null_manuid(data['UnitPrice21'])}, "
                + f"{no_null_categ(data['CateID2'])[1]}, "
                + f"{no_null_manuid(data['UnitID21'])}, "
                + f"{no_null_manuid(data['TaxID21'])}, "
            )
            query_db3 = (
                query_db3
                + query_temp
                + f"{no_null_categ(data['CateID3'])[0]}, "
                + f"{no_null_manuid(data['ManuID3'])}, "
                + f"{no_null_manuid(data['UnitCost3'])}, "
                + f"{no_null_manuid(data['UnitPrice31'])}, "
                + f"{no_null_categ(data['CateID3'])[1]}, "
                + f"{no_null_manuid(data['UnitID31'])}, "
                + f"{no_null_manuid(data['TaxID31'])}, "
            )
            query_db4 = (
                query_db4
                + query_temp
                + f"{no_null_categ(data['CateID4'])[0]}, "
                + f"{no_null_manuid(data['ManuID4'])}, "
                + f"{no_null_manuid(data['UnitCost4'])}, "
                + f"{no_null_manuid(data['UnitPrice41'])}, "
                + f"{no_null_categ(data['CateID4'])[1]}, "
                + f"{no_null_manuid(data['UnitID41'])}, "
                + f"{no_null_manuid(data['TaxID41'])}, "
            )

            for form_key, col in appended_keys:
                val = data.get(form_key)
                query_db1 = f"{query_db1}{no_null_manuid(val)}, "
                query_db2 = f"{query_db2}{no_null_manuid(val)}, "
                query_db3 = f"{query_db3}{no_null_manuid(val)}, "
                query_db4 = f"{query_db4}{no_null_manuid(val)}, "

            query_db1 = query_db1 + ")"
            query_db2 = query_db2 + ")"
            query_db3 = query_db3 + ")"
            query_db4 = query_db4 + ")"
            query_db1 = query_db1.replace(", )", ")")
            query_db2 = query_db2.replace(", )", ")")
            query_db3 = query_db3.replace(", )", ")")
            query_db4 = query_db4.replace(", )", ")")

            db_list: Dict[str:Any] = {
                "DB1": query_db1,
                "DB2": query_db2,
                "DB3": query_db3,
                "DB" + str(SCW_INDEX): query_db4,
            }
            dif_db_answ_list: List[str] = list()
            for i in db_list:
                db_name = i
                if db_name in answ_sku_list:
                    continue
                else:
                    with Session(engine[i]) as session:
                        session.execute(text(db_list[i]))
                        session.commit()
                    dif_db_answ_list.append(db_name)

            with Session(engine["DB1"]) as session1:
                stmt_Items_tbl_UnitPriceC = (
                    update(Items_tbl)
                    .values(
                        UnitPriceC=UnitCost2,
                    )
                    .where(Items_tbl.ProductSKU == ProductSKU)
                )
                answ_stmt_Items_tbl_UnitPriceC = session1.execute(
                    stmt_Items_tbl_UnitPriceC
                )
                session1.commit()

            with Session(engine["DB3"]) as session1:
                stmt_Items_tbl_UnitPriceC = (
                    update(Items_tbl)
                    .values(
                        UnitPriceC=UnitCost2,
                    )
                    .where(Items_tbl.ProductSKU == ProductSKU)
                )
                answ_stmt_Items_tbl_UnitPriceC = session1.execute(
                    stmt_Items_tbl_UnitPriceC
                )
                session1.commit()
            
            with Session(engine["DB4"]) as session1:
                stmt_Items_tbl_UnitPriceC = (
                    update(Items_tbl)
                    .values(
                        UnitPriceC=UnitCost2,
                    )
                    .where(Items_tbl.ProductSKU == ProductSKU)
                )
                answ_stmt_Items_tbl_UnitPriceC = session1.execute(
                    stmt_Items_tbl_UnitPriceC
                )
                session1.commit()

            return "dif_db", dif_db_answ_list
        elif identity_req == "invoices_tbl":
            query_invoice = data["QUERY"]
            try:
                df = pd.read_sql(query_invoice, engine[data["choicedb_source"]])
                answ_invoice = df.to_dict("records")
            except Exception as e:
                error_query = str(e.orig).split("[SQL Server]")[-1]
                return self.handle_exception(
                    FormValidationError({"QUERY": error_query, "total": "count + 1"})
                )
            answ_invoice1 = []
            totals = {}
            for count, i in enumerate(answ_invoice):
                answ__dict_temp = {}
                for i1 in i:
                    if i1 == "LineId":
                        answ__dict_temp["№"] = count + 1
                        continue
                    if isinstance(i[i1], int) or isinstance(i[i1], float):
                        if i1 in totals:
                            totals[i1].append(mod_value(i[i1]))
                        else:
                            totals[i1] = list()
                            totals[i1].append(mod_value(i[i1]))

                    answ__dict_temp[i1] = mod_value(i[i1])
                answ_invoice1.append(answ__dict_temp)
            if answ_invoice:
                totals.update({"Total": count + 1})
            else:
                totals.update({"Total": 0})

            for tot in totals:
                if tot != "Total":
                    totals.update({tot: round(sum(totals[tot]), 2)})
            return self.handle_exception(
                FormValidationError(
                    {"QUERY": {"QUERY": answ_invoice1, "total": totals}}
                )
            )

        elif identity_req == "quotations1_tbl":
            data = await self._arrange_data(request, data)
            if data["SourceDB"]:
                with Session(engine[engine_nick[data["SourceDB"]]]) as session:
                    request_init = request.__dict__["_form"]
                    query_answer_checkbusinessname = ""
                    if "_checkbusinessnamequotation_quotation" in request_init:
                        query_checkbusinessname = select(
                            Customers_tbl.__table__.columns
                        ).filter(
                            Customers_tbl.BusinessName.like(f"{data['BusinessName']}")
                        )
                        query_answer_checkbusinessname = (
                            session.execute(query_checkbusinessname).mappings().all()
                        )

                    elif "_checkaccountnoquotation_quotation" in request_init:
                        query_checkbusinessname = select(
                            Customers_tbl.__table__.columns
                        ).filter(Customers_tbl.AccountNo.like(f"{data['AccountNo']}"))
                        query_answer_checkbusinessname = (
                            session.execute(query_checkbusinessname).mappings().all()
                        )

                    if query_answer_checkbusinessname:
                        data.update(
                            {
                                "AccountNo": query_answer_checkbusinessname[0][
                                    "AccountNo"
                                ]
                            }
                        )
                        data.update(
                            {
                                "BusinessName": query_answer_checkbusinessname[0][
                                    "BusinessName"
                                ]
                            }
                        )

                    query_answer_productskudescription = ""
                    if "_productskudescription_quotation" in request_init:
                        query_productskudescription = select(
                            Items_tbl.__table__.columns
                        ).filter(
                            Items_tbl.ProductDescription.like(
                                f"{data['ProductDescription']}"
                            )
                        )
                        query_answer_productskudescription = (
                            session.execute(query_productskudescription)
                            .mappings()
                            .all()
                        )

                    elif "_productsku_quotation" in request_init:
                        query_productskudescription = select(
                            Items_tbl.__table__.columns
                        ).filter(Items_tbl.ProductSKU.like(f"{data['SKU']}"))

                        query_answer_productskudescription = (
                            session.execute(query_productskudescription)
                            .mappings()
                            .all()
                        )

                    if query_answer_productskudescription:
                        data.update(
                            {
                                "ProductDescription": query_answer_productskudescription[
                                    0
                                ][
                                    "ProductDescription"
                                ]
                            }
                        )
                        data.update(
                            {"SKU": query_answer_productskudescription[0]["ProductSKU"]}
                        )

                        data.update({"QTY": ""})
                        data.update(
                            {
                                "Price": float(
                                    query_answer_productskudescription[0]["UnitPrice"]
                                )
                            }
                        )
                        ProductUPC_source_db = query_answer_productskudescription[0][
                            "ProductUPC"
                        ]
                        ProductSKU_source_db = query_answer_productskudescription[0][
                            "ProductSKU"
                        ]

                    if data["SKU"] != None:
                        query_item_price = (
                            select(
                                InvoicesDetails_tbl.__table__.columns,
                                Invoices_tbl.AccountNo,
                            )
                            .join(
                                Invoices_tbl,
                                Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID,
                            )
                            .where(
                                and_(
                                    Invoices_tbl.AccountNo == data["AccountNo"],
                                    InvoicesDetails_tbl.ProductSKU == data["SKU"],
                                )
                            )
                            .order_by(InvoicesDetails_tbl.UnitPrice.desc())
                        )

                        answ_item_price = (
                            session.execute(query_item_price).mappings().all()
                        )
                        if answ_item_price:
                            data.update(
                                {"Price": float(answ_item_price[0]["UnitPrice"])}
                            )
            with Session(engine["DB1"]) as session:
                if query_answer_productskudescription:
                    query_qtydb1 = select(Items_tbl.__table__.columns).filter(
                        Items_tbl.ProductUPC.like(ProductUPC_source_db)
                    )

                    answer_qtydb1 = session.execute(query_qtydb1).mappings().all()
                    if answer_qtydb1:
                        data.update({"qty_db": int(answer_qtydb1[0]["QuantOnHand"])})
            with Session(engine["DB_admin"]) as session:
                if query_answer_productskudescription:
                    query_qtyadmin = select(
                        func.sum(QuotationDetails.QTY).label("qty_admin")
                    ).filter(
                        and_(
                            QuotationDetails.ProductSKU.like(ProductSKU_source_db),
                            QuotationDetails.InvoiceNumber != None,
                        )
                    )
                    answer_qtyadmin1 = session.execute(query_qtyadmin).mappings().all()
            return "create_new_quotation", data
        elif identity_req == "quotations2_tbl":
            data = await self._arrange_data(request, data)
            return "list_all_quotation", data
        elif identity_req == "quotations3_tbl":
            data = await self._arrange_data(request, data)
            return "create_new_quotation_edit", data
        elif identity_req == "quotationsdetails1_tbl":
            data = await self._arrange_data(request, data)
            return "edit_quotation", data
        elif identity_req == "upload_file":
            data = await self._arrange_data(request, data)
            return "upload_files", data
        elif identity_req == "checkinvertory":
            data = await self._arrange_data(request, data)
            return "checkinvertory", data

        elif identity_req == "items_massupdate":
            data = await self._arrange_data(request, data)
            return "items_massupdate", data

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data, True)
            await self.validate(request, data)
            session = session_init(request)

            obj = await self.find_by_pk(request, pk)
            session.add(await self._populate_obj(request, obj, data, True))
            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                await anyio.to_thread.run_sync(session.commit)
                await anyio.to_thread.run_sync(session.refresh, obj)
            return obj
        except Exception as e:
            self.handle_exception(e)

    async def edit1(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        pk = request.__dict__["scope"]["path"].split("/")[-1]
        [data.update({i: "2023-08-01 00:00:00"}) for i in column_list_date]
        [data.update({i: ""}) for i in column_list_str]
        [data.update({i: 0}) for i in column_list_zero]
        [data.update({i: 1}) for i in column_list_one]
        query_db1 = "UPDATE [Items_tbl] SET [CateID]="
        query_db2 = "UPDATE [Items_tbl] SET [CateID]="
        query_db3 = "UPDATE [Items_tbl] SET [CateID]="
        query_db4 = "UPDATE [Items_tbl] SET [CateID]="
        query_db1 = (
            query_db1
            + f"{no_null_categ(data['CateID1'])[0]}, [ManuID]={no_null_manuid(data['ManuID1'])}, [UnitCost]={no_null_manuid(data['UnitCost1'])}, [UnitPrice]={no_null_manuid(data['UnitPrice11'])}, [SubCateID]={no_null_categ(data['CateID1'])[1]}, [UnitID]={no_null_manuid(data['UnitID11'])}, [ItemTaxID]={no_null_manuid(data['TaxID11'])},"
        )
        query_db2 = (
            query_db2
            + f"{no_null_categ(data['CateID2'])[0]}, [ManuID]={no_null_manuid(data['ManuID2'])}, [UnitCost]={no_null_manuid(data['UnitCost2'])}, [UnitPrice]={no_null_manuid(data['UnitPrice21'])}, [SubCateID]={no_null_categ(data['CateID2'])[1]}, [UnitID]={no_null_manuid(data['UnitID21'])}, [ItemTaxID]={no_null_manuid(data['TaxID21'])},"
        )
        query_db3 = (
            query_db3
            + f"{no_null_categ(data['CateID3'])[0]}, [ManuID]={no_null_manuid(data['ManuID3'])}, [UnitCost]={no_null_manuid(data['UnitCost3'])}, [UnitPrice]={no_null_manuid(data['UnitPrice31'])}, [SubCateID]={no_null_categ(data['CateID3'])[1]}, [UnitID]={no_null_manuid(data['UnitID31'])}, [ItemTaxID]={no_null_manuid(data['TaxID31'])},"
        )
        query_db4 = (
            query_db4
            + f"{no_null_categ(data['CateID4'])[0]}, [ManuID]={no_null_manuid(data['ManuID4'])}, [UnitCost]={no_null_manuid(data['UnitCost4'])}, [UnitPrice]={no_null_manuid(data['UnitPrice41'])}, [SubCateID]={no_null_categ(data['CateID4'])[1]}, [UnitID]={no_null_manuid(data['UnitID41'])}, [ItemTaxID]={no_null_manuid(data['TaxID41'])},"
        )
        if data:
            import re

            suf_re = re.compile(r"(\d+)$")
            existing = set(re.findall(r"\[([^\]]+)\]", query_db1))
            alias_map = {
                "TaxID": "ItemTaxID",
                "UnitQty": "CountInUnit",
                "ManuName": "ManuID",
                "CategoryName": "CateID",
                "SubCateName": "SubCateID",
                "UnitDesc": "UnitID",
                "Qty": "QuantOnHand",
            }
            for key in data:
                if key in miss_list or key in cate_dif_db:
                    continue
                val = data[key]
                base = suf_re.sub("", key)
                col = alias_map.get(base, base)
                if col in existing:
                    continue
                query_db1 = f"{query_db1}[{col}]={no_null_manuid(val)}, "
                query_db2 = f"{query_db2}[{col}]={no_null_manuid(val)}, "
                query_db3 = f"{query_db3}[{col}]={no_null_manuid(val)}, "
                query_db4 = f"{query_db4}[{col}]={no_null_manuid(val)}, "
                existing.add(col)
        query_temp = "WHERE [Items_tbl].[ProductID] = "
        query_db1 = query_db1 + query_temp + f"{pk}"
        query_db2 = query_db2 + query_temp + f"{pk}"
        query_db3 = query_db3 + query_temp + f"{pk}"
        query_db4 = query_db4 + query_temp + f"{pk}"
        query_db1 = query_db1.replace(", WHERE", " WHERE")
        query_db2 = query_db2.replace(", WHERE", " WHERE")
        query_db3 = query_db3.replace(", WHERE", " WHERE")
        query_db4 = query_db4.replace(", WHERE", " WHERE")
        import time

        with Session(engine["DB1"]) as session:
            answ = session.execute(text(query_db1))
            session.commit()
        with Session(engine["DB2"]) as session:
            session.execute(text(query_db2))
            session.commit()
        with Session(engine["DB3"]) as session:
            session.execute(text(query_db3))
            session.commit()
        with Session(engine["DB4"]) as session:
            session.execute(text(query_db4))
            session.commit()
        return answ

    async def _arrange_data(
        self,
        request: Request,
        data: Dict[str, Any],
        is_edit: bool = False,
    ) -> Dict[str, Any]:
        miss_fields = ["Prodtempl1", "Prodtempl2", "Prodtempl3", "Prodtempl4"]
        arranged_data: Dict[str, Any] = {}
        for field in self.fields:
            if field.name in miss_fields:
                continue
            if (is_edit and field.exclude_from_edit) or (
                not is_edit and field.exclude_from_create
            ):
                continue
            if isinstance(field, RelationField) and data[field.name] is not None:
                foreign_model = self._find_foreign_model(field.identity)  # type: ignore
                if not field.multiple:
                    arranged_data[field.name] = await foreign_model.find_by_pk(
                        request, data[field.name]
                    )
                else:
                    arranged_data[field.name] = await foreign_model.find_by_pks(
                        request, data[field.name]
                    )
            else:
                arranged_data[field.name] = data[field.name]
        return arranged_data

    async def _populate_obj(
        self,
        request: Request,
        obj: Any,
        data: Dict[str, Any],
        is_edit: bool = False,
    ) -> Any:
        for field in self.fields:
            if (is_edit and field.exclude_from_edit) or (
                not is_edit and field.exclude_from_create
            ):
                continue
            name, value = field.name, data.get(field.name, None)
            if isinstance(field, FileField):
                value, should_be_deleted = value
                if should_be_deleted:
                    setattr(obj, name, None)
                elif (not field.multiple and value is not None) or (
                    field.multiple and isinstance(value, list) and len(value) > 0
                ):
                    setattr(obj, name, value)
            else:
                setattr(obj, name, value)
        return obj

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        objs = await self.find_by_pks(request, pks)

        for i in session_list:
            session: Union[Session, AsyncSession] = i
            for obj in objs:
                await anyio.to_thread.run_sync(session.delete, obj)
            await anyio.to_thread.run_sync(session.commit)
        return len(objs)

    async def build_full_text_search_query(
        self, request: Request, term: str, model: Any
    ) -> Any:
        return self.get_search_query(request, term)

    def handle_exception(self, exc: Exception) -> None:
        try:
            sqlalchemy_file = __import__("sqlalchemy_file")
            if isinstance(exc, sqlalchemy_file.exceptions.ValidationError):
                raise FormValidationError({exc.key: exc.msg})
        except ImportError:
            pass
        raise exc
