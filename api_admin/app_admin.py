import os
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette_admin.contrib.sqla import Admin
from sqlalchemy.orm import Session
from database import Base, engine
from config import SECRET, CORS_ORIGINS
from admins.model import AdminUserProject_admin, AdminDBs_admin, UsersSessions
from admins.schemas import *
from admins.view import (
    AdminDBs_adminView,
    AdminUserProject_adminView,
    UsersSessionsView,
)
from starlette_admin.views import Link
from admins.provider import MyAuthProvider
from storage import configure_storage
from starlette.requests import Request
from starlette_admin.contrib.sqla.ext.pydantic import ModelView

app = Starlette(
    routes=[
        Mount("/static", app=StaticFiles(directory="static"), name="static"),
        Route("/", lambda r: RedirectResponse(url="/admin")),
    ],
    on_startup=[configure_storage],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

admin = Admin(
    engine["DB_admin"],
    title="Warehouse Management",
    base_url="/admin",
    statics_dir="static",
    login_logo_url="/admin/statics/logo_fcs.png",  # base_url + '/statics/' + path_to_the_file
    auth_provider=MyAuthProvider(allow_paths=["/statics/logo_fcs.png"]),
    middlewares=[Middleware(SessionMiddleware, secret_key=SECRET, max_age=7800)],
)
admin.add_view(
    AdminUserProject_adminView(
        AdminUserProject_admin,
        icon="fa fa-users",
        label="Admin Users",
        identity="adminuserproject_admin",
    )
)
admin.add_view(
    AdminDBs_adminView(
        AdminDBs_admin,
        icon="fa fa-database",
        label="Admin DBs",
        identity="admindbs_admin",
    )
)
admin.add_view(
    UsersSessionsView(
        UsersSessions,
        icon="fa fa-sitemap",
        label="Users Sessions",
        identity="users_sessions",
    )
)

admin.add_view(Link("Project", url="/project", icon="fa fa-link"))
admin.mount_to(app)
