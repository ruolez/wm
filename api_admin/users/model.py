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

from .. import Base







class Items_tbl(Base):
    __tablename__ = "Items_tbl"

    ProductID = Column(Integer, primary_key=True, nullable=False)
    CateID = Column(Integer, nullable=True)
    SubCateID = Column(Integer, nullable=True)
    ProductDescription = Column(String, nullable=True)
    ProductSKU = Column(String, nullable=True)
    ProductUPC = Column(String, nullable=True)
    UnitCost = Column(Integer, nullable=True)
    UnitPrice = Column(Integer, nullable=True)
    ItemWeight = Column(String, nullable=True)
    SPPromoted = Column(Integer, default=0)


class Manufacturers_tbl(Base):
    __tablename__ = "Manufacturers_tbl"

    ManufacturerID = Column(Integer, primary_key=True, nullable=False)
    ManuName = Column(String, nullable=True)





