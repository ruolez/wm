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
    Float,
)

from .. import relationship, backref, Base2


class Categories_db2_tbl(Base2):
    __tablename__ = "Categories_db2_tbl"

    CategoryID = Column(Integer, primary_key=True, nullable=False)
    CategoryNo = Column(Integer, nullable=True)
    CategoryName = Column(String, nullable=True)
    UseAsAcctType = Column(Integer, nullable=False, default=0)




