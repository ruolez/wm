import datetime
import urllib
from urllib.parse import parse_qsl
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, and_, asc, desc, or_
from sqlalchemy import func
from api1.api_v2.utils import get_time_range_limit
from api1.users.model import (
    AdminUserProject_admin,
    Invoices_tbl,
    Terms_tbl,
    Shippers_tbl,
    Customers_tbl,
    Employees_tbl,
    AccountSyncSetting,
)


class InvoiceHandler:
    def __init__(self, request, user_account, user_account_status, engine, engine_nick):
        self.request = request
        self.user_account = user_account
        self.user_account_status = user_account_status
        self.engine = engine
        self.engine_nick = engine_nick
        self.query_params = self._parse_query_params()

    def _parse_query_params(self):
        raw = self.request.scope.get("query_string", b"").decode("utf-8")
        return dict(parse_qsl(urllib.parse.unquote_plus(raw)))

    def _get_user_databases(self):
        with Session(self.engine["DB_admin"]) as s:
            dbs = s.execute(
                select(AdminUserProject_admin.accessdb)
                .filter_by(username=self.user_account)
            ).scalar()
        return dbs.split("/") if dbs else []

    def _get_allowed_names(self, db_alias):
        with Session(self.engine["DB_admin"]) as s:
            src_id = s.execute(
                select(AdminUserProject_admin.id)
                .filter_by(username=self.user_account)
            ).scalar_one_or_none() or 0
            synced = s.execute(
                select(AccountSyncSetting.target_username)
                .where(
                    AccountSyncSetting.db_name == db_alias,
                    AccountSyncSetting.source_user_id == src_id,
                    AccountSyncSetting.sync_enabled == True
                )
            ).scalars().all()
        primary = [self.user_account.lower()]
        return list({n.lower() for n in synced} | set(primary))

    def _build_invoice_query(self, labelq, allowed_names):
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(weeks=get_time_range_limit())
        q = (
            select(
                Invoices_tbl.InvoiceID,
                Invoices_tbl.InvoiceNumber,
                Invoices_tbl.InvoiceTotal,
                Invoices_tbl.InvoiceDate,
                Invoices_tbl.AccountNo,
                Invoices_tbl.ShippingCost,
                Invoices_tbl.CustomerID,
                Invoices_tbl.TrackingNo,
                Invoices_tbl.Notes,
                labelq.label("FirstName"),
                func.db_name().label("DBname"),
                Shippers_tbl.Shipper.label("Shipper"),
                Terms_tbl.TermDescription.label("TermDescription"),
                Customers_tbl.BusinessName.label("Customer"),
                (Invoices_tbl.InvoiceTotal - Invoices_tbl.TotalCredits - Invoices_tbl.TotalPayments).label("Balance"),
            )
            .join(Terms_tbl, Invoices_tbl.TermID == Terms_tbl.TermID, isouter=True)
            .join(Shippers_tbl, Invoices_tbl.ShipperID == Shippers_tbl.ShipperID, isouter=True)
            .join(Customers_tbl, Invoices_tbl.CustomerID == Customers_tbl.CustomerID, isouter=True)
            .where(and_(Invoices_tbl.InvoiceDate > cutoff, Invoices_tbl.Void == 0))
        )
        if "manager" not in self.user_account_status.split("/"):
            q = (
                q.join(Employees_tbl, Invoices_tbl.SalesRepID == Employees_tbl.EmployeeID)
                 .where(
                     and_(
                         Invoices_tbl.InvoiceDate > cutoff,
                         func.lower(Employees_tbl.FirstName).in_(allowed_names)
                     )
                 )
            )
        for field, val in self.query_params.items():
            if hasattr(Invoices_tbl, field):
                q = q.where(getattr(Invoices_tbl, field) == val)
        if "order_by" in self.query_params:
            col, dir_ = self.query_params["order_by"].split(" ")
            if hasattr(Invoices_tbl, col):
                q = q.order_by(asc(getattr(Invoices_tbl, col))) if dir_.lower() == "asc" else q.order_by(desc(getattr(Invoices_tbl, col)))
        else:
            q = q.order_by(Invoices_tbl.InvoiceDate.desc())
        return q

    def find_all(self):
        dbs = self._get_user_databases()
        if not dbs:
            return []
        out = []
        for db in dbs:
            if "dop" in self.query_params and self.engine_nick.get(db) != self.query_params["dop"]:
                continue
            eng_key = self.engine_nick.get(db)
            if not eng_key:
                continue
            allowed = self._get_allowed_names(db)
            labelq = (
                select(Employees_tbl.FirstName)
                .where(Invoices_tbl.SalesRepID == Employees_tbl.EmployeeID)
                .correlate(Invoices_tbl)
                .scalar_subquery()
            )
            with Session(self.engine[eng_key]) as s:
                q = self._build_invoice_query(labelq, allowed)
                out.extend(s.execute(q).mappings().all())
        return out

    def filter_by(self, filters):
        self.query_params.update(filters)
        return self.find_all()
