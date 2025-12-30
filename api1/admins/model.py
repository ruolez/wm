import enum
from datetime import datetime

from typing import List, Optional, Union
from sqlalchemy_file import File, ImageField, FileField

from starlette.requests import Request
from sqlalchemy_file.validators import ContentTypeValidator, SizeValidator
from pydantic import AnyHttpUrl, BaseModel, EmailStr

from sqlalchemy_utils import (
    EmailType,
    IPAddressType,
    URLType,
    UUIDType,
)

from ..helpers import UploadFile

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

from .. import Base


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


class Article(Base):
    __tablename__ = "Article"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Enum(Status))


class AdminUserProject(Base):
    __tablename__ = "AdminUserProject"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    password = Column(String(100), nullable=True)
    statususer = Column(Enum(StatusUsers))
    activated = Column(Boolean, default=True)
    email = Column(EmailType)
    avatar = Column(
        ImageField(
            upload_storage="avatar",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("200k")],
        ),
        nullable=True,
    )

class AdminDBs(Base):
    __tablename__ = "AdminDBs"

    id = Column(Integer, primary_key=True, nullable=False)
    TypeDB = Column(Enum(AdminDBsType), nullable=False)
    Username = Column(String, nullable=False)
    Password = Column(String, nullable=False)
    ipAddress = Column(IPAddressType)
    ShareName = Column(String, nullable=True, default="")
    Port = Column(Integer, nullable=False)
    NameDB = Column(String, nullable=False)


