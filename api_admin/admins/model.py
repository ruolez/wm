import enum
from datetime import datetime

from typing import List, Optional, Union
from sqlalchemy_file import File, ImageField, FileField

from starlette.requests import Request
from sqlalchemy_file.validators import ContentTypeValidator, SizeValidator
from pydantic import AnyHttpUrl, BaseModel, EmailStr

from sqlalchemy.orm import Mapped, mapped_column, declared_attr, relationship

from sqlalchemy_utils import (
    EmailType,
    IPAddressType,
    URLType,
    UUIDType,
)

from helpers import UploadFile

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Unicode,
    Boolean,
    JSON,
)

from database import Base_admin


class Status(str, enum.Enum):
    Draft = "d"
    Published = "p"
    Withdrawn = "w"


class StatusUsers(str, enum.Enum):
    admin = "Admin"
    regular_user = "Regular user"


class AdminDBsType(str, enum.Enum):
    mssql = "Microsoft SQL Server"


AVAILABLE_USER_TYPES = [
    ("admin", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]


class Article(Base_admin):
    __tablename__ = "Article"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Enum(Status))


class admin_menu(Base_admin):
    __tablename__ = "admin_menu"

    id: Mapped[int] = mapped_column(primary_key=True)
    model: Mapped[str] = mapped_column(nullable=True, default="")
    label: Mapped[str] = mapped_column(nullable=True, default="")
    users: Mapped[str] = mapped_column(nullable=True, default="")
    status: Mapped[str] = mapped_column(nullable=True, default="")
    description: Mapped[str] = mapped_column(nullable=True, default="")
    flag: Mapped[bool] = mapped_column(nullable=True, default=0)


class admin_menu_list(Base_admin):
    __tablename__ = "admin_menu_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    menu: Mapped[str] = mapped_column(nullable=True, default="")
    status: Mapped[str] = mapped_column(nullable=True, default="")
    description: Mapped[str] = mapped_column(nullable=True, default="")
    flag: Mapped[bool] = mapped_column(nullable=True, default=0)


class AdminUserProject_admin(Base_admin):
    __tablename__ = "AdminUserProject_admin"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    password = Column(String(100), nullable=True)
    accessmenu = Column(String(255))
    accessdb = Column(String(255))
    dop1 = Column(String(255))
    dop2 = Column(String(255))
    dop3 = Column(String(255))
    statususer = Column(String(255))
    activated = Column(Boolean, default=0)
    email = Column(EmailType)


class UsersSessions(Base_admin):
    __tablename__ = "UsersSessions"

    id = Column(Integer, primary_key=True, nullable=False)
    session_id: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[str] = mapped_column(nullable=True)
    user_name: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    browser_info: Mapped[str] = mapped_column(nullable=True)
    data: Mapped[str] = mapped_column(nullable=True)
    Comment: Mapped[str] = mapped_column(nullable=True)
    Notes: Mapped[str] = mapped_column(nullable=True)
    Flag1: Mapped[bool] = mapped_column(nullable=True, default=1)
    Flag2: Mapped[bool] = mapped_column(nullable=True)
    Flag3: Mapped[bool] = mapped_column(nullable=True)
    Dop1: Mapped[str] = mapped_column(nullable=True)
    Dop2: Mapped[str] = mapped_column(nullable=True)
    Dop3: Mapped[str] = mapped_column(nullable=True)


class AdminDBs_admin(Base_admin):
    __tablename__ = "AdminDBs_admin"

    id = Column(Integer, primary_key=True, nullable=False)
    TypeDB = Column(Enum(AdminDBsType), nullable=False)
    Username = Column(String, nullable=False)
    Password = Column(String, nullable=False)
    ipAddress = Column(String)
    ShareName = Column(String, nullable=True, default="")
    Port = Column(Integer, nullable=False, default=1433)
    NameDB = Column(String, nullable=False)
    Nick = Column(String, nullable=False)
    dop1 = Column(String, nullable=False)
    dop2 = Column(String, nullable=False)
    dop3 = Column(String, nullable=False)
    dop4 = Column(String, nullable=False)
    interval_1 = Column(String, nullable=False)
    interval_2 = Column(String, nullable=False)
    interval_3 = Column(String, nullable=False)
    interval_4 = Column(String, nullable=False)
    time_1 = Column(String, nullable=False)
    time_2 = Column(String, nullable=False)
    time_3 = Column(String, nullable=False)
    time_4 = Column(String, nullable=False)
    activated_shed: Mapped[bool] = mapped_column(nullable=True, default=1)
    activated_shed_1: Mapped[bool] = mapped_column(nullable=True, default=1)
    activated_dop: Mapped[bool] = mapped_column(nullable=True, default=0)
    activated_dop_1: Mapped[bool] = mapped_column(nullable=True, default=0)


class shed_admin(Base_admin):
    __tablename__ = "shed_admin"

    id = Column(Integer, primary_key=True, nullable=False)
    Description = Column(String, nullable=False)
    Status = Column(String, nullable=False)
    Number = Column(Integer, nullable=False, default=1433)
    Name = Column(String, nullable=False)
    Nick = Column(String, nullable=False)
    dop1 = Column(String, nullable=False)
    dop2 = Column(String, nullable=False)
    dop3 = Column(String, nullable=False)
    dop4 = Column(String, nullable=False)
    activated_shed: Mapped[bool] = mapped_column(nullable=True, default=1)
    time_1 = Column(String, nullable=False)
    interval_1 = Column(String, nullable=False)
    time_1 = Column(String, nullable=False)

    activated_shed_1: Mapped[bool] = mapped_column(nullable=True, default=1)
    time_2 = Column(String, nullable=False)

    interval_2 = Column(String, nullable=False)
    interval_3 = Column(String, nullable=False)
    interval_4 = Column(String, nullable=False)
    time_3 = Column(String, nullable=False)
    time_4 = Column(String, nullable=False)
    activated_dop: Mapped[bool] = mapped_column(nullable=True, default=0)
    activated_dop_1: Mapped[bool] = mapped_column(nullable=True, default=0)
