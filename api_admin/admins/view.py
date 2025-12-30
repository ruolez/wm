from typing import Any, List, Dict

from sqlalchemy.orm import Session
from starlette_admin import action
from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from starlette_admin import (
    EnumField,
    ExportType,
    StringField,
    EnumField_multy,
    BooleanField,
    IntegerField,
)
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import FormValidationError


from .model import (
    AdminDBs_admin,
    UsersSessions,
    admin_menu,
    admin_menu_list,
    AdminUserProject_admin,
    shed_admin,
)


from . import engine
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete


AVAILABLE_USER_TYPES = [
    ("admin", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]

AVAILABLE_USER_TYPES_1 = [
    ("admin", "Admin"),
    ("regularuser", "Regular user"),
    ("commiteruser", "Commiter/Regular user"),
    ("packer", "Packer user"),
    ("checker", "Checker user"),
    ("manager", "Manager"),
]

AVAILABLE_USER_TYPES_DB = [
    ("mssql", "mssql"),
]


AVAILABLE_Menu = list()
AVAILABLE_Menu_dict = dict()
AVAILABLE_Menu_dict_rev = dict()
AVAILABLE_DB = list()
AVAILABLE_DB_dict = dict()

with Session(engine["DB_admin"]) as session:
    stmt_select_insert_alias = select(admin_menu_list.__table__.columns)
    rows = session.execute(stmt_select_insert_alias).mappings().all()

    for i in rows:

        AVAILABLE_Menu_temp = list()

        AVAILABLE_Menu_temp.append(i["description"])
        AVAILABLE_Menu_temp.append(i["description"])
        AVAILABLE_Menu_dict[i["description"]] = i["description"]
        AVAILABLE_Menu_dict_rev[i["description"]] = i["menu"]
        AVAILABLE_Menu.append(tuple(AVAILABLE_Menu_temp))

    stmt_select_db = select(AdminDBs_admin.__table__.columns)
    rows_select_db = session.execute(stmt_select_db).mappings().all()

    for i in rows_select_db:

        AVAILABLE_DB_temp = list()

        AVAILABLE_DB_temp.append(i["Nick"])
        AVAILABLE_DB_temp.append(i["Nick"])
        AVAILABLE_DB_dict[i["Nick"]] = i["Nick"]
        AVAILABLE_DB.append(tuple(AVAILABLE_DB_temp))


class AdminDBs_adminView(ModelView):

    fields = [
        "id",
        "Nick",
        EnumField(
            "TypeDB",
            choices=AVAILABLE_USER_TYPES_DB,
            select2=False,
            label="TypeDB",
            help_text="Add Type DB",
        ),
        StringField("Username", label="Username Name", help_text="Add Username"),
        "Password",
        "ipAddress",
        "ShareName",
        "NameDB",
        BooleanField(
            "activated_shed", label="Invoice Creation - CRON", help_text="on/off cron"
        ),
        IntegerField(
            "dop1", label="Start Invoice Number", help_text="Add Invoice Number"
        ),
        IntegerField("interval_1", label="Interval", help_text="(seconds)"),
        IntegerField("time_1", label="Days Back", help_text="Add integer"),
        BooleanField(
            "activated_shed_1",
            label="Invoice UPDATE / VOID - CRON",
            help_text="on/off cron",
        ),
        IntegerField("interval_2", label="Interval", help_text="(minutes)"),
        IntegerField("time_2", label="Days Back", help_text="Add integer"),
        BooleanField(
            "activated_dop",
            label="CreditMemos Creation - CRON",
            help_text="on/off cron",
        ),
        IntegerField(
            "dop2", label="Start CreditMemos ID", help_text="Add CreditMemos ID"
        ),
        IntegerField("interval_3", label="Interval", help_text="(seconds)"),
    ]
    fields_default_sort = [AdminDBs_admin.id, ("id", True)]


class AdminUserProject_adminView(ModelView):
    fields = [
        "id",
        "username",
        "full_name",
        "password",
        EnumField_multy(
            "accessmenu", choices=AVAILABLE_Menu, select2=False, label="Access Menu"
        ),
        EnumField_multy(
            "accessdb", choices=AVAILABLE_DB, select2=False, label="Access DB"
        ),
        EnumField_multy(
            "statususer",
            choices=AVAILABLE_USER_TYPES_1,
            select2=False,
            label="User Roles",
        ),
        "email",
    ]
    fields_default_sort = [AdminUserProject_admin.username, ("username", True)]


class UsersSessionsView(ModelView):
    fields = [
        BooleanField("Flag1", label="Active", help_text="Delete Session"),
        "user_name",
        "created_at",
        "updated_at",
        "expires_at",
        "browser_info",
    ]
    fields_default_sort = [UsersSessions.id, ("user_name", True)]


class ArticleView(ModelView):

    def can_view_details(self, request: Request) -> bool:
        print(request.state.user, "read_requesttttttttttttttt")
        return "read" in request.state.user["roles"]

    def can_create(self, request: Request) -> bool:
        print(request.state.user, "create_requesttttttttttttttt")
        return "create" in request.state.user["roles"]

    def can_edit(self, request: Request) -> bool:
        print(request.state.user, "edit_requesttttttttttttttt")
        return "edit" in request.state.user["roles"]

    def can_delete(self, request: Request) -> bool:
        print(request.state.user, "delete_requesttttttttttttttt")
        return "delete" in request.state.user["roles"]

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "action_make_published" in request.state.user["roles"]
        return await super().is_action_allowed(request, name)

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        for article in await self.find_by_pks(request, pks):
            article.status = Status.Published
            session.add(article)
        session.commit()
        return f"{len(pks)} articles were successfully marked as published"
