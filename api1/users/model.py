import enum
from datetime import datetime

import os, sys

sys.path.insert(1, os.path.join(sys.path[0], ".."))

from typing import List, Optional, Union
from sqlalchemy_file import File, ImageField, FileField

from starlette.requests import Request
from sqlalchemy_file.validators import ContentTypeValidator, SizeValidator
from pydantic import AnyHttpUrl, BaseModel, EmailStr

from sqlalchemy.orm import Mapped, mapped_column, declared_attr

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
    func,
    Index,
)


from sqlalchemy.orm import declarative_base, relationship, backref

Base = declarative_base()


class Status(str, enum.Enum):
    PENDING = "pending"
    REJECTED = "rejected"
    APPROVED = "approved"


class StatusUsers(str, enum.Enum):
    admin = "Admin"
    regular_user = "Regular user"


class AdminUserProject_admin(Base):
    __tablename__ = "AdminUserProject_admin"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255))
    accessmenu: Mapped[str] = mapped_column(String(255))
    accessdb = Column(String(255))
    dop1 = Column(String(255))
    dop2 = Column(String(255))
    dop3 = Column(String(255))
    activated: Mapped[bool]
    email: Mapped[str] = mapped_column(String(255))
    statususer = Column(String(255))
    default_home_page: Mapped[str] = mapped_column(String(255), nullable=True)


class AdminDBs_admin(Base):
    __tablename__ = "AdminDBs_admin"

    id = Column(Integer, primary_key=True, nullable=False)
    TypeDB: Mapped[str] = mapped_column(String(255))
    Username = Column(String, nullable=True)
    Password = Column(String, nullable=True)
    ipAddress = Column(String)
    ShareName = Column(String, nullable=True, default="")
    Port = Column(Integer, nullable=True, default=1433)
    NameDB = Column(String, nullable=True)
    Nick = Column(String, nullable=True)
    dop1 = Column(String, nullable=True)
    dop2 = Column(String, nullable=True)
    dop3 = Column(String, nullable=True)
    dop4 = Column(String, nullable=True)
    interval_1 = Column(String, nullable=True)
    interval_2 = Column(String, nullable=True)
    interval_3 = Column(String, nullable=True)
    interval_4 = Column(String, nullable=True)
    time_1 = Column(String, nullable=True)
    time_2 = Column(String, nullable=True)
    time_3 = Column(String, nullable=True)
    time_4 = Column(String, nullable=True)
    activated_shed: Mapped[bool] = mapped_column(nullable=True, default=1)
    activated_shed_1: Mapped[bool] = mapped_column(nullable=True, default=1)
    activated_dop: Mapped[bool] = mapped_column(nullable=True, default=0)
    activated_dop_1: Mapped[bool] = mapped_column(nullable=True, default=0)


class shed_admin(Base):
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


class admin_query(Base):
    __tablename__ = "admin_query"

    alias = Column(String, nullable=True, primary_key=True)
    data = Column(String, nullable=True)


class admin_menu(Base):
    __tablename__ = "admin_menu"

    id: Mapped[int] = mapped_column(primary_key=True)
    model: Mapped[str] = mapped_column(nullable=True, default="")
    label: Mapped[str] = mapped_column(nullable=True, default="")
    users: Mapped[str] = mapped_column(nullable=True, default="")
    status: Mapped[str] = mapped_column(nullable=True, default="")
    description: Mapped[str] = mapped_column(nullable=True, default="")
    flag: Mapped[bool] = mapped_column(nullable=True, default=0)


class admin_menu_list(Base):
    __tablename__ = "admin_menu_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    menu: Mapped[str] = mapped_column(nullable=True, default="")
    status: Mapped[str] = mapped_column(nullable=True, default="")
    description: Mapped[str] = mapped_column(nullable=True, default="")
    flag: Mapped[bool] = mapped_column(nullable=True, default=0)


class QuotationsTemp(Base):
    __tablename__ = "QuotationsTemp"

    id: Mapped[int] = mapped_column(primary_key=True)
    SessionID: Mapped[str] = mapped_column(String(255))
    SourceDB: Mapped[str] = mapped_column(String(255))
    AccountNo: Mapped[str] = mapped_column(String(255))
    BusinessName: Mapped[str] = mapped_column(String(255))
    ProductDescription: Mapped[str] = mapped_column(String(255))
    SKU: Mapped[str] = mapped_column(String(255))
    QTY: Mapped[int]
    Price: Mapped[int]
    Total: Mapped[int]


class SubCategories_tbl(Base):
    __tablename__ = "Subcategories_tbl"

    SubCateID = Column(Integer, primary_key=True, nullable=False)
    SubCateName = Column(String, nullable=True)
    CategoryID = Column(Integer, nullable=True)
    dep_key = Column(Integer, nullable=True, default=0)
    color_code = Column(String, nullable=True)
    key_Postion = Column(Integer, nullable=True, default=0)


class Manufacturers_tbl(Base):
    __tablename__ = "Manufacturers_tbl"

    ManufacturerID = Column(Integer, primary_key=True, nullable=False)
    ManuName = Column(String, nullable=True)


class Categories_tbl(Base):
    __tablename__ = "Categories_tbl"

    CategoryID = Column(Integer, primary_key=True, nullable=False)
    CategoryNo = Column(Integer, nullable=True)
    CategoryName = Column(String, nullable=True)
    UseAsAcctType = Column(Integer, nullable=False, default=0)


class Quotation(Base):
    __tablename__ = "Quotation"

    id: Mapped[int] = mapped_column(primary_key=True)
    QuotationNumber: Mapped[str] = mapped_column(String(255), nullable=True)
    Status: Mapped[str] = mapped_column(String(255), nullable=True)
    BusinessName: Mapped[str] = mapped_column(String(255), nullable=True)
    # AccountNo: Mapped[str] = mapped_column(String(255), nullable=True)
    InvoiceNumber: Mapped[str] = mapped_column(String(255), nullable=True)
    Notes: Mapped[bool] = mapped_column(nullable=True)
    SalesRepresentative: Mapped[str] = mapped_column(String(255), nullable=True)
    Description: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    Employee: Mapped[str] = mapped_column(String(255), nullable=True)
    DateCreate: Mapped[datetime]
    LastUpdate: Mapped[datetime]
    SourceDB: Mapped[str] = mapped_column(String(255), nullable=True)
    FlagOrder: Mapped[bool]


class QuotationTest(Base):
    __tablename__ = "QuotationTest"

    id: Mapped[int] = mapped_column(primary_key=True)
    QuotationNumber: Mapped[str] = mapped_column(String(255), nullable=True)
    Status: Mapped[str] = mapped_column(String(255), nullable=True)
    BusinessName: Mapped[str] = mapped_column(String(255), nullable=True)
    # AccountNo: Mapped[str] = mapped_column(String(255), nullable=True)
    InvoiceNumber: Mapped[str] = mapped_column(String(255), nullable=True)
    Notes: Mapped[bool] = mapped_column(nullable=True)
    SalesRepresentative: Mapped[str] = mapped_column(String(255), nullable=True)
    Description: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    Employee: Mapped[str] = mapped_column(String(255), nullable=True)
    DateCreate: Mapped[datetime]
    LastUpdate: Mapped[datetime]
    SourceDB: Mapped[str] = mapped_column(String(255), nullable=True)
    FlagOrder: Mapped[bool]


class QuotationsStatus(Base):
    __tablename__ = "QuotationsStatus"

    id: Mapped[int] = mapped_column(primary_key=True)
    DateCreate: Mapped[datetime]
    QuotationNumber: Mapped[str] = mapped_column(String(255), nullable=True)
    Status: Mapped[str] = mapped_column(String(255), nullable=True)
    BusinessName: Mapped[str] = mapped_column(String(255), nullable=True)
    AccountNo: Mapped[str] = mapped_column(String(255), nullable=True)
    InvoiceNumber: Mapped[str] = mapped_column(String(255), nullable=True)
    Notes: Mapped[bool] = mapped_column(nullable=True)
    SalesRep: Mapped[str] = mapped_column(String(255), nullable=True)
    Packer: Mapped[str] = mapped_column(String(255), nullable=True)
    Checker: Mapped[str] = mapped_column(String(255), nullable=True)
    Username: Mapped[str] = mapped_column(String(255), nullable=True)
    UserStatus: Mapped[str] = mapped_column(String(255), nullable=True)
    LastUpdate: Mapped[datetime]
    TotalQty: Mapped[int] = mapped_column(nullable=True)
    SourceDB: Mapped[str] = mapped_column(String(255), nullable=True)
    Shipto: Mapped[str] = mapped_column(String(255), nullable=True)
    ShipAddress1: Mapped[str] = mapped_column(String(255), nullable=True)
    ShipAddress2: Mapped[str] = mapped_column(String(255), nullable=True)
    ShipContact: Mapped[str] = mapped_column(String(255), nullable=True)
    ShipCity: Mapped[str] = mapped_column(String(255), nullable=True)
    ShipState: Mapped[str] = mapped_column(String(255), nullable=True)
    ShipZipCode: Mapped[str] = mapped_column(String(255), nullable=True)
    ShipPhoneNo: Mapped[str] = mapped_column(String(255), nullable=True)
    ShipperID: Mapped[str] = mapped_column(String(255), nullable=True)
    TermID: Mapped[str] = mapped_column(String(255), nullable=True)
    QuotationTotal: Mapped[str] = mapped_column(String(255), nullable=True)
    Comment: Mapped[str] = mapped_column(String(255), nullable=True)
    Flag1: Mapped[bool]
    Flag2: Mapped[bool]
    Flag3: Mapped[bool]
    Dop1: Mapped[str] = mapped_column(String(255), nullable=True)
    Dop2: Mapped[str] = mapped_column(String(255), nullable=True)
    Dop3: Mapped[str] = mapped_column(String(255), nullable=True)


class UsersSessions(Base):
    __tablename__ = "UsersSessions"

    id = Column(Integer, primary_key=True, nullable=False)
    session_id: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[str] = mapped_column(nullable=True)
    user_name: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(nullable=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=True)
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


class Missitems(Base):
    __tablename__ = "Missitems"

    id = Column(Integer, primary_key=True, nullable=False)
    ProductDescription: Mapped[str] = mapped_column(nullable=True)
    ProductSKU: Mapped[str] = mapped_column(nullable=True)
    ProductUPC: Mapped[str] = mapped_column(nullable=True)
    startDate: Mapped[datetime] = mapped_column(nullable=True)
    endDate: Mapped[datetime] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(nullable=True)
    Notes: Mapped[str] = mapped_column(nullable=True)
    Flag1: Mapped[bool] = mapped_column(nullable=True, default=1)
    Flag2: Mapped[bool] = mapped_column(nullable=True)
    Dop1: Mapped[str] = mapped_column(nullable=True)
    Dop2: Mapped[str] = mapped_column(nullable=True)


class QuotationDetails(Base):
    __tablename__ = "QuotationDetails"
    id: Mapped[int] = mapped_column(primary_key=True)
    DateCreate = Column(DateTime, default=datetime.utcnow)
    DateDop = Column(DateTime)
    DateDop_1 = Column(DateTime)
    QuotationID: Mapped[int] = mapped_column(nullable=True)
    QuotationNumber: Mapped[str] = mapped_column(nullable=True)
    InvoiceNumber: Mapped[str] = mapped_column(nullable=True)
    ProductDescription: Mapped[str] = mapped_column(nullable=True)
    ProductSKU: Mapped[str] = mapped_column(nullable=True)
    ProductUPC: Mapped[str] = mapped_column(nullable=True)
    QTY: Mapped[int] = mapped_column(nullable=True)
    FlagOrder: Mapped[bool] = mapped_column(nullable=True)
    FieldDop_1: Mapped[str] = mapped_column(nullable=True)
    FieldDop_2: Mapped[str] = mapped_column(nullable=True)
    FieldDop_3: Mapped[str] = mapped_column(nullable=True)
    FieldDop_4: Mapped[str] = mapped_column(nullable=True)


class QuotationDetailsTest(Base):
    __tablename__ = "QuotationDetailsTest"
    id: Mapped[int] = mapped_column(primary_key=True)
    DateCreate = Column(DateTime, default=datetime.utcnow)
    DateDop = Column(DateTime)
    DateDop_1 = Column(DateTime)
    QuotationID: Mapped[int] = mapped_column(nullable=True)
    QuotationNumber: Mapped[str] = mapped_column(nullable=True)
    InvoiceNumber: Mapped[str] = mapped_column(nullable=True)
    ProductDescription: Mapped[str] = mapped_column(nullable=True)
    ProductSKU: Mapped[str] = mapped_column(nullable=True)
    ProductUPC: Mapped[str] = mapped_column(nullable=True)
    QTY: Mapped[int] = mapped_column(nullable=True)
    FlagOrder: Mapped[bool] = mapped_column(nullable=True)
    FieldDop_1: Mapped[str] = mapped_column(nullable=True)
    FieldDop_2: Mapped[str] = mapped_column(nullable=True)
    FieldDop_3: Mapped[str] = mapped_column(nullable=True)
    FieldDop_4: Mapped[str] = mapped_column(nullable=True)


class Invoices_tbl(Base):
    __tablename__ = "Invoices_tbl"

    InvoiceID = Column(Integer, primary_key=True, nullable=False)
    InvoiceDate = Column(DateTime, default=datetime.utcnow)
    BusinessName = Column(String, nullable=False)
    InvoiceNumber = Column(String, nullable=False)
    InvoiceType = Column(String, default="")
    InvoiceTitle = Column(String, default="")
    CustomerID = Column(Integer, default=0)
    AccountNo = Column(String, default="")
    PoNumber = Column(String, default="")
    ShipDate = Column(DateTime, default=datetime.utcnow)
    Shipto = Column(String, default="")
    ShipAddress1 = Column(String, default="")
    ShipAddress2 = Column(String, default="")
    ShipContact = Column(String, default="")
    ShipCity = Column(String, default="")
    ShipState = Column(String, default="")
    ShipZipCode = Column(String, default="")
    ShipPhoneNo = Column(String, default="")
    DriverID = Column(Integer, default=0)
    TermID = Column(Integer, default=0)
    SalesRepID = Column(Integer, default=0)
    TermID = Column(Integer, default=0)
    ShipperID = Column(Integer, default=0)
    TrackingNo = Column(String, default="")
    ShippingCost = Column(Integer, default=0)
    TotQtyOrd = Column(Integer, default=0)
    TotQtyShp = Column(Integer, default=0)
    TotQtyRtrnd = Column(Integer, default=0)
    NoLines = Column(Integer, default=0)
    NoBoxes = Column(Integer, default=0)
    TotalWeight = Column(Integer, default=0)
    TotalDiscounts = Column(Integer, default=0)
    InvoiceSubtotal = Column(Integer, default=0)
    TotalTaxes = Column(Integer, default=0)
    OtherCharges = Column(Integer, default=0)
    InvoiceTotal = Column(Integer, default=0)
    TotalCredits = Column(Integer, default=0)
    TotalPayments = Column(Integer, default=0)
    OrderPrinted: Mapped[bool] = mapped_column(default=0)
    InvoicePrinted: Mapped[bool] = mapped_column(default=0)
    PackingSlipPrinted: Mapped[bool] = mapped_column(default=0)
    PickListPrinted: Mapped[bool] = mapped_column(default=0)
    Imported: Mapped[bool] = mapped_column(default=0)
    Pos: Mapped[bool] = mapped_column(default=0)
    Notes: Mapped[str] = mapped_column(String(255), default="")
    Header: Mapped[str] = mapped_column(String(255), default="")
    Footer: Mapped[str] = mapped_column(String(255), default="")
    Void: Mapped[bool] = mapped_column(default=0)


class InvoicesDetails_tbl(Base):
    __tablename__ = "InvoicesDetails_tbl"

    LineID = Column(Integer, primary_key=True, nullable=False)
    InvoiceID = Column(Integer, nullable=True)
    QtyShipped = Column(Integer, nullable=True)
    CateID = Column(Integer, nullable=True)
    SubCateID = Column(Integer, nullable=True)
    ProductID = Column(Integer, nullable=True)
    UnitPrice = Column(Integer, nullable=True)
    ProductSKU = Column(String, nullable=False)
    ProductUPC = Column(String, nullable=False)
    ProductDescription = Column(String, nullable=False)
    UnitDesc: Mapped[str] = mapped_column(String(255), default="")
    UnitQty: Mapped[int] = mapped_column(default=1)
    ProductID: Mapped[int] = mapped_column(default=0)
    ProductSKU: Mapped[str] = mapped_column(String(255), default="")
    ProductUPC: Mapped[str] = mapped_column(String(255), default="")
    ProductDescription: Mapped[str] = mapped_column(String(255), default="")
    ItemSize: Mapped[str] = mapped_column(String(255), default="")
    LineMessage: Mapped[str] = mapped_column(String(255), default="")
    UnitPrice: Mapped[float] = mapped_column(default=0)
    OriginalPrice: Mapped[float] = mapped_column(default=0)
    RememberPrice: Mapped[bool] = mapped_column(default=0)
    UnitCost: Mapped[float] = mapped_column(default=0)
    Discount: Mapped[int] = mapped_column(default=0)
    ds_Percent: Mapped[bool] = mapped_column(default=0)
    QtyShipped: Mapped[int] = mapped_column(default=0)
    QtyOrdered: Mapped[int] = mapped_column(default=0)
    ItemWeight: Mapped[str] = mapped_column(String(255), default="")
    Packing: Mapped[str] = mapped_column(String(255), default="")
    ExtendedPrice: Mapped[float] = mapped_column(default=0)
    ExtendedDisc: Mapped[float] = mapped_column(default=0)
    ExtendedCost: Mapped[float] = mapped_column(default=0)
    PromotionID: Mapped[int] = mapped_column(default=0)
    PromotionLine: Mapped[bool] = mapped_column(default=0)
    PromotionDescription: Mapped[str] = mapped_column(String(255), nullable=True)
    PromotionAmount: Mapped[float] = mapped_column(nullable=True)
    ActExtendedPrice: Mapped[float] = mapped_column(default=0)
    SPPromoted: Mapped[bool] = mapped_column(default=0)
    SPPromotionDescription: Mapped[str] = mapped_column(String(255), default="")
    Taxable: Mapped[bool] = mapped_column(default=0)
    ItemTaxID: Mapped[int] = mapped_column(default=0)
    Catch: Mapped[int] = mapped_column(default=0)
    Negative: Mapped[bool] = mapped_column(default=0)
    Flag: Mapped[bool] = mapped_column(default=0)
    Void: Mapped[bool] = mapped_column(default=0)


class Invoices2_tbl(Base):
    __tablename__ = "Invoices2_tbl"

    InvoiceID = Column(Integer, primary_key=True, nullable=False)
    InvoiceDate = Column(DateTime, default=datetime.utcnow)
    BusinessName = Column(String, nullable=False)
    InvoiceNumber = Column(String, nullable=False)
    CustomerID = Column(Integer, default=0)
    AccountNo = Column(String, default="")
    SalesRepID = Column(Integer, default=0)
    ShipperID = Column(Integer, default=0)
    TrackingNo = Column(String, default="")
    ShippingCost = Column(Integer, default=0)
    InvoiceTotal = Column(Integer, default=0)
    TotalCredits = Column(Integer, default=0)
    TotalPayments = Column(Integer, default=0)
    Notes: Mapped[str] = mapped_column(String(255), default="")


class Items_tbl(Base):
    __tablename__ = "Items_tbl"

    ProductID = Column(Integer, primary_key=True, nullable=False)
    SubCateID = Column(Integer, nullable=True)
    ProductDescription = Column(String, nullable=False)
    ProductSKU = Column(String, nullable=True)
    ProductUPC = Column(String, nullable=True)
    UnitCost = Column(Integer, nullable=True)
    UnitPrice = Column(Integer, nullable=True)
    ItemWeight = Column(String, nullable=True, default=0)
    UnitPriceC = Column(String, nullable=True, default=0)
    SPPromoted = Column(Integer, default=0)
    QuantOnHand = Column(Integer, nullable=True)
    CateID = Column(Integer, nullable=True)
    UnitID = Column(Integer, nullable=True)
    ReorderLevel = Column(Integer, nullable=True)
    UnitPrice = Column(Integer, nullable=True)
    ItemSize = Column(String, nullable=True, default=0)
    Discontinued: Mapped[bool]
    ExpDate: Mapped[datetime]


class Items_BinLocations(Base):
    __tablename__ = "Items_BinLocations"

    id = Column(Integer, primary_key=True, nullable=False)
    CreatedAt: Mapped[datetime]
    ProductUPC = Column(String(255), nullable=True)
    ProductDescription = Column(String(255), nullable=True)
    Qty_Cases = Column(Integer, nullable=True)
    BinLocationID = Column(Integer, nullable=True)
    LastUpdate: Mapped[datetime]
    int1 = Column(Integer, nullable=True)
    txt1 = Column(String(255), nullable=True)


class BinLocations_tbl(Base):
    __tablename__ = "BinLocations_tbl"

    BinLocationID = Column(Integer, primary_key=True, nullable=False)
    BinLocation = Column(String(50), nullable=True)


class Employees_tbl(Base):
    __tablename__ = "Employees_tbl"

    EmployeeID = Column(Integer, primary_key=True, nullable=False)
    FirstName = Column(String, nullable=False)


class Quotations_tbl(Base):
    __tablename__ = "Quotations_tbl"

    QuotationID = Column(Integer, primary_key=True, nullable=False)
    QuotationNumber = Column(String, nullable=True)
    QuotationDate: Mapped[datetime] = mapped_column(
        server_default=func.now(), default=datetime.utcnow
    )
    ExpirationDate: Mapped[datetime]
    SalesRepID = Column(Integer, nullable=True)
    AutoOrderNo = Column(String, nullable=True)
    ExpirationDate = Column(DateTime)
    CustomerID = Column(Integer, nullable=True)
    BusinessName = Column(String, nullable=True)
    AccountNo = Column(String, nullable=True)
    Shipto = Column(String, nullable=True)
    ShipAddress1 = Column(String, nullable=True)
    ShipAddress2 = Column(String, nullable=True)
    ShipContact = Column(String, nullable=True)
    ShipCity = Column(String, nullable=True)
    ShipState = Column(String, nullable=True)
    ShipZipCode = Column(String, nullable=True)
    ShipPhoneNo = Column(String, nullable=True)
    QuotationTotal = Column(Integer, nullable=True)
    ShipperID: Mapped[int] = mapped_column(default=1)
    flaged: Mapped[bool] = mapped_column(default=0)
    TermID: Mapped[int]
    Status: Mapped[int] = mapped_column(default=1)
    QuotationTitle: Mapped[str] = mapped_column(default="", nullable=True)
    PoNumber: Mapped[str] = mapped_column(default="", nullable=True)
    Header: Mapped[str] = mapped_column(default="", nullable=True)
    Footer: Mapped[str] = mapped_column(default="", nullable=True)
    Notes: Mapped[str] = mapped_column(default="", nullable=True)
    Memo: Mapped[str] = mapped_column(default="", nullable=True)
    TotalTaxes = Column(Integer, default=0)


class Quotations1_tbl(Base):
    __tablename__ = "Quotations1_tbl"

    id = Column(Integer, primary_key=True, nullable=False)
    QuotationNumber = Column(String, nullable=True)
    SalesRepID = Column(Integer, nullable=True)
    AutoOrderNo = Column(String, nullable=True)
    QuotationDate = Column(DateTime)
    ExpirationDate = Column(DateTime)
    CustomerID = Column(Integer, nullable=True)
    BusinessName = Column(String, nullable=True)
    AccountNo = Column(String, nullable=True)
    Shipto = Column(String, nullable=True)
    ShipAddress1 = Column(String, nullable=True)
    ShipAddress2 = Column(String, nullable=True)
    ShipContact = Column(String, nullable=True)
    ShipCity = Column(String, nullable=True)
    ShipState = Column(String, nullable=True)
    ShipZipCode = Column(String, nullable=True)
    ShipPhoneNo = Column(String, nullable=True)
    QuotationTotal = Column(Integer, nullable=True)
    ShipperID: Mapped[int] = mapped_column(default=1)
    flaged: Mapped[bool] = mapped_column(default=0)
    TermID: Mapped[int]
    Status: Mapped[int] = mapped_column(default=1)


class Quotations2_tbl(Base):
    __tablename__ = "Quotations2_tbl"

    QuotationID = Column(Integer, primary_key=True, nullable=False)
    QuotationNumber = Column(String, nullable=True)
    SalesRepID = Column(Integer, nullable=True)
    AutoOrderNo = Column(String, nullable=True)
    QuotationDate = Column(DateTime)
    ExpirationDate = Column(DateTime)
    CustomerID = Column(Integer, nullable=True)
    BusinessName = Column(String, nullable=True)
    AccountNo = Column(String, nullable=True)
    Shipto = Column(String, nullable=True)
    ShipAddress1 = Column(String, nullable=True)
    ShipAddress2 = Column(String, nullable=True)
    ShipContact = Column(String, nullable=True)
    ShipCity = Column(String, nullable=True)
    ShipState = Column(String, nullable=True)
    ShipZipCode = Column(String, nullable=True)
    ShipPhoneNo = Column(String, nullable=True)
    QuotationTotal = Column(Integer, nullable=True)
    ShipperID: Mapped[int] = mapped_column(default=1)
    flaged: Mapped[bool] = mapped_column(default=0)
    TermID: Mapped[int]
    Status: Mapped[int] = mapped_column(default=1)
    TotalAmount = Column(String, nullable=True)
    Total: Mapped[int]
    DBname: Mapped[str]
    FirstName: Mapped[str]
    choicedb_source: Mapped[str]
    ProfitMargin: Mapped[float]


class Quotations3_tbl(Base):
    __tablename__ = "Quotations3_tbl"

    LineID = Column(Integer, primary_key=True, nullable=False)
    QuotationID = Column(Integer, nullable=True)
    CateID = Column(Integer, nullable=True)
    SubCateID = Column(Integer, nullable=True)
    ProductID = Column(Integer, nullable=True)
    ExpDate = Column(DateTime, nullable=True)
    Flag = Column(Boolean, nullable=True)
    Taxable = Column(Boolean, nullable=True)
    ItemTaxID = Column(Integer, nullable=True)
    Catch = Column(Integer, nullable=True)
    ActExtendedPrice = Column(Integer, nullable=True)
    SPPromoted = Column(Boolean, nullable=True)
    PromotionLine = Column(Integer, nullable=True)
    PromotionID = Column(Integer, nullable=True)
    ExtendedCost = Column(Integer, nullable=True)
    ExtendedDisc = Column(Integer, nullable=True)
    ExtendedPrice = Column(Integer, nullable=True)
    ds_Percent = Column(Integer, nullable=True)
    Discount = Column(Integer, nullable=True)
    UnitCost = Column(Integer, nullable=True)
    UnitPrice = Column(Integer, nullable=True)
    OriginalPrice = Column(Integer, nullable=True)
    QuotationID = Column(Integer, nullable=True)
    ProductSKU = Column(String, nullable=True)
    ProductUPC = Column(String, nullable=True)
    ProductDescription = Column(String, nullable=True)
    ItemSize = Column(String, nullable=True)
    Qty = Column(String, nullable=True)
    ItemWeight = Column(String, nullable=True)
    ItemTaxID = Column(String, nullable=True)
    UnitDesc = Column(String, default="", nullable=True)
    ReasonID = Column(String, default="", nullable=True)
    LineMessage = Column(String, default="", nullable=True)
    SPPromotionDescription = Column(String, default="", nullable=True)
    Comments = Column(String, default="", nullable=True)
    RememberPrice = Column(String, default=0, nullable=True)
    UnitQty: Mapped[int] = mapped_column(default=1)
    PromotionDescription: Mapped[str] = mapped_column(String(255), nullable=True)
    PromotionAmount: Mapped[float] = mapped_column(nullable=True)


class Customers_tbl(Base):
    __tablename__ = "Customers_tbl"

    CustomerID: Mapped[int] = mapped_column(primary_key=True)
    BusinessName: Mapped[str] = mapped_column(String(255))
    AccountNo: Mapped[str] = mapped_column(String(255))
    Shipto: Mapped[str] = mapped_column(String(255))
    Address1: Mapped[str] = mapped_column(String(255))
    Address2: Mapped[str] = mapped_column(String(255))
    City: Mapped[str] = mapped_column(String(255))
    State: Mapped[str] = mapped_column(String(255))
    ZipCode: Mapped[str] = mapped_column(String(255))
    Phone_Number: Mapped[str] = mapped_column(String(255))
    Contactname: Mapped[str] = mapped_column(String(255))
    ShipContact: Mapped[str] = mapped_column(String(255))
    ShipAddress1: Mapped[str] = mapped_column(String(255))
    ShipAddress2: Mapped[str] = mapped_column(String(255))
    ShipPhone_Number: Mapped[str] = mapped_column(String(255))
    ShipCity: Mapped[str] = mapped_column(String(255))
    ShipState: Mapped[str] = mapped_column(String(255))
    ShipZipCode: Mapped[str] = mapped_column(String(255))
    Phone_Number: Mapped[str] = mapped_column(String(255))
    SalesRepID: Mapped[int]
    Memo: Mapped[str] = mapped_column(String(255))
    Notes: Mapped[str] = mapped_column(String(255))
    TermID: Mapped[int]
    Discontinued: Mapped[bool] = mapped_column(default=0)


class Units_tbl(Base):
    __tablename__ = "Units_tbl"

    UnitID: Mapped[int] = mapped_column(primary_key=True)
    UnitDesc: Mapped[str] = mapped_column(String(50))


class QuotationsDetails_tbl(Base):
    __tablename__ = "QuotationsDetails_tbl"

    LineID = Column(Integer, primary_key=True, nullable=False)
    QuotationID = Column(Integer, nullable=True)
    CateID = Column(Integer, nullable=True)
    SubCateID = Column(Integer, nullable=True)
    ProductID = Column(Integer, nullable=True)
    ExpDate = Column(DateTime, nullable=True)
    Flag = Column(Boolean, nullable=True)
    Taxable = Column(Boolean, nullable=True)
    ItemTaxID = Column(Integer, nullable=True)
    Catch = Column(Integer, nullable=True)
    ActExtendedPrice = Column(Integer, nullable=True)
    SPPromoted = Column(Boolean, nullable=True)
    PromotionLine = Column(Integer, nullable=True)
    PromotionID = Column(Integer, nullable=True)
    ExtendedCost = Column(Integer, nullable=True)
    ExtendedDisc = Column(Integer, nullable=True)
    ExtendedPrice = Column(Integer, nullable=True)
    ds_Percent = Column(Integer, nullable=True)
    Discount = Column(Integer, nullable=True)
    UnitCost = Column(Integer, nullable=True)
    UnitPrice = Column(Integer, nullable=True)
    OriginalPrice = Column(Integer, nullable=True)
    QuotationID = Column(Integer, nullable=True)
    ProductSKU = Column(String, nullable=True)
    ProductUPC = Column(String, nullable=True)
    ProductDescription = Column(String, nullable=True)
    ItemSize = Column(String, nullable=True)
    Qty = Column(String, nullable=True)
    ItemWeight = Column(String, nullable=True)
    ItemTaxID = Column(String, nullable=True)
    UnitDesc = Column(String, default="", nullable=True)
    ReasonID = Column(String, default="", nullable=True)
    LineMessage = Column(String, default="", nullable=True)
    SPPromotionDescription = Column(String, default="", nullable=True)
    Comments = Column(String, default="", nullable=True)
    RememberPrice = Column(String, default=0, nullable=True)
    UnitQty: Mapped[int] = mapped_column(default=1)
    PromotionDescription: Mapped[str] = mapped_column(String(255), nullable=True)
    PromotionAmount: Mapped[float] = mapped_column(nullable=True)


class Quotationsdetails1_tbl(Base):
    __tablename__ = "Quotationsdetails1_tbl"

    LineID = Column(Integer, primary_key=True, nullable=False)
    QuotationID = Column(Integer, nullable=True)
    CateID = Column(Integer, nullable=True)
    SubCateID = Column(Integer, nullable=True)
    ProductID = Column(Integer, nullable=True)
    ExpDate = Column(DateTime, nullable=True)
    Flag = Column(Boolean, nullable=True)
    Taxable = Column(Boolean, nullable=True)
    ItemTaxID = Column(Integer, nullable=True)
    Catch = Column(Integer, nullable=True)
    ActExtendedPrice = Column(Integer, nullable=True)
    SPPromoted = Column(Boolean, nullable=True)
    PromotionLine = Column(Integer, nullable=True)
    PromotionID = Column(Integer, nullable=True)
    ExtendedCost = Column(Integer, nullable=True)
    ExtendedDisc = Column(Integer, nullable=True)
    ExtendedPrice = Column(Integer, nullable=True)
    ds_Percent = Column(Integer, nullable=True)
    Discount = Column(Integer, nullable=True)
    UnitCost = Column(Integer, nullable=True)
    UnitPrice = Column(Integer, nullable=True)
    OriginalPrice = Column(Integer, nullable=True)
    QuotationID = Column(Integer, nullable=True)
    ProductSKU = Column(String, nullable=True)
    ProductUPC = Column(String, nullable=True)
    ProductDescription = Column(String, nullable=True)
    ItemSize = Column(String, nullable=True)
    Qty = Column(String, nullable=True)
    ItemWeight = Column(String, nullable=True)
    ItemTaxID = Column(String, nullable=True)
    UnitDesc = Column(String, default="", nullable=True)
    ReasonID = Column(String, default="", nullable=True)
    LineMessage = Column(String, default="", nullable=True)
    SPPromotionDescription = Column(String, default="", nullable=True)
    Comments = Column(String, default="", nullable=True)
    RememberPrice = Column(String, default=0, nullable=True)
    UnitQty: Mapped[int] = mapped_column(default=1)
    PromotionDescription: Mapped[str] = mapped_column(String(255), nullable=True)
    PromotionAmount: Mapped[float] = mapped_column(nullable=True)


class UploadFile(Base):
    __tablename__ = "upload_file"
    id = Column(Integer, primary_key=True, nullable=False)

    cover = Column(
        ImageField(
            upload_storage="cover",
            thumbnail_size=(128, 128),
            validators=[SizeValidator("1M")],
        )
    )
    document = Column(
        FileField(
            upload_storage="document",
            validators=[
                SizeValidator("5M"),
                ContentTypeValidator(
                    allowed_content_types=[
                        "application/msword",
                    ]
                ),
            ],
        )
    )

    multiple_files = Column(
        FileField(
            multiple=True,
            validators=[SizeValidator("100k")],
        )
    )


class errorcheckinvertory(Base):
    __tablename__ = "errorcheckinvertory"

    id = Column(Integer, primary_key=True, nullable=False)
    CateID = Column(String, nullable=True)


class CheckInvertory(Base):
    __tablename__ = "checkinvertory"

    id = Column(Integer, primary_key=True, nullable=False)
    CateID = Column(String, nullable=True)
    SubCateID = Column(String, nullable=True)
    ProductUPC = Column(String, nullable=True)
    ProductDescription = Column(String, nullable=True)
    DB = Column(String, nullable=True)
    Status = Column(String, nullable=True)


class Orders(Base):
    __tablename__ = "Orders"

    OrderNumber = Column(Integer, primary_key=True, nullable=False)
    OrderDate = Column(DateTime, nullable=True)


class OrderDetails(Base):
    __tablename__ = "Order Details"

    OrderNumber = Column(Integer, primary_key=True, nullable=False)
    Product = Column(String, nullable=True)
    QuantityShipped = Column(Integer, nullable=True)


class Inventory(Base):
    __tablename__ = "Inventory"

    LocalSKU = Column(Integer, primary_key=True, nullable=False)
    Barcode = Column(String, nullable=True)
    ItemName = Column(String, nullable=True)


class Tracking(Base):
    __tablename__ = "Tracking"

    AutoNumber = Column(Integer, primary_key=True, nullable=False)
    OrderNum = Column(String, nullable=True)
    TrackingID = Column(String, nullable=True)


class PurchaseOrders_tbl(Base):
    __tablename__ = "PurchaseOrders_tbl"

    PoID: Mapped[int] = mapped_column(primary_key=True)
    PoDate: Mapped[datetime]
    RequiredDate: Mapped[datetime]
    Status: Mapped[int] = mapped_column(nullable=True, default=0)
    SupplierID: Mapped[int] = mapped_column(nullable=True)
    PoNumber: Mapped[str] = mapped_column(nullable=True, default="")
    BusinessName: Mapped[str] = mapped_column(nullable=True, default="")
    AccountNo: Mapped[str] = mapped_column(nullable=True, default="")
    PoTotal: Mapped[int] = mapped_column(nullable=True)
    EmployeeID: Mapped[int] = mapped_column(nullable=True)
    TermID: Mapped[int] = mapped_column(nullable=True)
    NoLines: Mapped[int] = mapped_column(nullable=True)
    ShipperID: Mapped[int] = mapped_column(nullable=True)
    TotQtyOrd: Mapped[int] = mapped_column(nullable=True)
    TotQtyRcv: Mapped[int] = mapped_column(nullable=True)
    Notes = Column(String, nullable=True)
    PoTitle: Mapped[str] = mapped_column(nullable=True, default="")
    Shipto: Mapped[str] = mapped_column(nullable=True, default="")
    ShipAddress1: Mapped[str] = mapped_column(nullable=True, default="")
    ShipAddress2: Mapped[str] = mapped_column(nullable=True, default="")
    ShipContact: Mapped[str] = mapped_column(nullable=True, default="")
    ShipCity: Mapped[str] = mapped_column(nullable=True, default="")
    ShipState: Mapped[str] = mapped_column(nullable=True, default="")
    ShipZipCode: Mapped[str] = mapped_column(nullable=True, default="")
    ShipPhoneNo: Mapped[str] = mapped_column(nullable=True, default="")


class PurchaseOrdersDetails_tbl(Base):
    __tablename__ = "PurchaseOrdersDetails_tbl"
    LineID = Column(Integer, primary_key=True, nullable=False)
    PoID = Column(Integer, nullable=True)
    ProductDescription = Column(String, nullable=True)
    ProductUPC = Column(String, nullable=True)
    ProductSKU = Column(String, nullable=True)
    UnitCost = Column(Integer, nullable=True)
    ExtendedCost = Column(Integer, nullable=True)
    ProductID: Mapped[int] = mapped_column(nullable=True)
    CateID: Mapped[int] = mapped_column(nullable=True)
    SubCateID: Mapped[int] = mapped_column(nullable=True)
    QtyOrdered: Mapped[int] = mapped_column(nullable=True)
    QtyReceived: Mapped[int] = mapped_column(nullable=True)
    UnitQty: Mapped[int] = mapped_column(nullable=True)
    ExpDate: Mapped[str] = mapped_column(nullable=True, default="")
    UnitDesc = Column(String, default="", nullable=True)


class Suppliers_tbl(Base):
    __tablename__ = "Suppliers_tbl"

    SupplierID = Column(Integer, primary_key=True, nullable=False)
    AccountNo = Column(String, nullable=True)
    BusinessName = Column(String, nullable=True)
    Address1 = Column(String, nullable=True)
    Address2 = Column(String, nullable=True)
    State = Column(String, nullable=True)
    ZipCode = Column(String, nullable=True)
    Phone_Number = Column(String, nullable=True)
    Contactname = Column(String, nullable=True)
    Email = Column(String, nullable=True)


class pick_list_products(Base):
    __tablename__ = "pick_list_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_pick_list: Mapped[int] = mapped_column(nullable=True)
    amount: Mapped[int] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(nullable=False)
    sku: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)
    barcode: Mapped[str] = mapped_column(nullable=True, default="")


class pick_lists(Base):
    __tablename__ = "pick_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    date_from: Mapped[datetime]
    cdate: Mapped[datetime]
    mdate: Mapped[datetime]
    is_orders_gathered: Mapped[int] = mapped_column(nullable=True)
    is_products_gathered: Mapped[int] = mapped_column(nullable=True)
    is_printed: Mapped[int] = mapped_column(nullable=True)
    is_locked: Mapped[int] = mapped_column(nullable=True)
    excluded_orders: Mapped[str] = mapped_column(nullable=False)


class AuditLog(Base):
    __tablename__ = "AuditLog"

    sessionID: Mapped[int] = mapped_column(primary_key=True)
    QuotationID: Mapped[int] = mapped_column(nullable=True)
    quotationDB: Mapped[str] = mapped_column(nullable=False)
    userID: Mapped[str] = mapped_column(nullable=False)
    startDate: Mapped[datetime]
    endDate: Mapped[datetime]
    username: Mapped[str] = mapped_column(nullable=False)
    eventType: Mapped[str] = mapped_column(nullable=False)
    isClosed: Mapped[bool] = mapped_column(nullable=True, default=0)
    clientIP: Mapped[str] = mapped_column(nullable=False)
    Comment: Mapped[str] = mapped_column(nullable=False)
    Notes: Mapped[str] = mapped_column(nullable=False)
    Flag1: Mapped[bool] = mapped_column(nullable=True, default=0)
    Flag2: Mapped[bool] = mapped_column(nullable=True, default=0)
    Flag3: Mapped[bool] = mapped_column(nullable=True, default=0)
    Dop1: Mapped[str] = mapped_column(nullable=False)
    Dop2: Mapped[str] = mapped_column(nullable=False)
    Dop3: Mapped[str] = mapped_column(nullable=False)
    Dop4: Mapped[str] = mapped_column(nullable=False)


class ManualInventoryUpdate(Base):
    __tablename__ = "manualinventoryupdate"

    id: Mapped[int] = mapped_column(primary_key=True)
    DateCreated: Mapped[datetime]
    Username: Mapped[str] = mapped_column(nullable=False)
    UserStatus: Mapped[str] = mapped_column(nullable=True, default="")
    UpdateType: Mapped[str] = mapped_column(nullable=False)
    ProductDescription: Mapped[str] = mapped_column(String(255), nullable=True)
    OldDescription: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    NewDescription: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    ProductSKU: Mapped[str] = mapped_column(String(255), nullable=True)
    OldSKU: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    NewSKU: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    ProductUPC: Mapped[str] = mapped_column(String(255), nullable=True)
    OldUPC: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    NewUPC: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    OldQty: Mapped[int] = mapped_column(nullable=True)
    NewQty: Mapped[int] = mapped_column(nullable=True)
    DiffQty: Mapped[int] = mapped_column(nullable=True)
    OldPrice: Mapped[float] = mapped_column(nullable=True)
    NewPrice: Mapped[float] = mapped_column(nullable=True)
    DiffPrice: Mapped[float] = mapped_column(nullable=True)
    OldCost: Mapped[float] = mapped_column(nullable=True)
    NewCost: Mapped[float] = mapped_column(nullable=True)
    DiffCost: Mapped[float] = mapped_column(nullable=True)
    OldPriceB: Mapped[float] = mapped_column(nullable=True)
    NewPriceB: Mapped[float] = mapped_column(nullable=True)
    DiffPriceB: Mapped[float] = mapped_column(nullable=True)
    flag1: Mapped[bool] = mapped_column(nullable=True, default=0)
    flag2: Mapped[bool] = mapped_column(nullable=True, default=0)
    flag3: Mapped[bool] = mapped_column(nullable=True, default=0)
    tmp1: Mapped[str] = mapped_column(nullable=True, default="")
    tmp2: Mapped[str] = mapped_column(nullable=True, default="")
    tmp3: Mapped[str] = mapped_column(nullable=True, default="")


class OrdersLock(Base):
    __tablename__ = "orderslock"

    id: Mapped[int] = mapped_column(primary_key=True)


class PurchaseOrder(Base):
    __tablename__ = "purchaseorder"

    id: Mapped[int] = mapped_column(primary_key=True)
    DateCreated: Mapped[datetime]
    Username: Mapped[str] = mapped_column(nullable=False)
    UserStatus: Mapped[str] = mapped_column(nullable=True, default="")
    UpdateType: Mapped[str] = mapped_column(nullable=False)
    ProductDescription: Mapped[str] = mapped_column(String(255), nullable=True)
    OldDescription: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    NewDescription: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    ProductSKU: Mapped[str] = mapped_column(String(255), nullable=True)
    OldSKU: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    NewSKU: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    ProductUPC: Mapped[str] = mapped_column(String(255), nullable=True)
    OldUPC: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    NewUPC: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    OldQty: Mapped[int] = mapped_column(nullable=True)
    NewQty: Mapped[int] = mapped_column(nullable=True)
    DiffQty: Mapped[int] = mapped_column(nullable=True)
    OldPrice: Mapped[float] = mapped_column(nullable=True)
    NewPrice: Mapped[float] = mapped_column(nullable=True)
    DiffPrice: Mapped[float] = mapped_column(nullable=True)
    OldCost: Mapped[float] = mapped_column(nullable=True)
    NewCost: Mapped[float] = mapped_column(nullable=True)
    DiffCost: Mapped[float] = mapped_column(nullable=True)
    OldPriceB: Mapped[float] = mapped_column(nullable=True)
    NewPriceB: Mapped[float] = mapped_column(nullable=True)
    DiffPriceB: Mapped[float] = mapped_column(nullable=True)
    flag1: Mapped[bool] = mapped_column(nullable=True, default=0)
    flag2: Mapped[bool] = mapped_column(nullable=True, default=0)
    flag3: Mapped[bool] = mapped_column(nullable=True, default=0)
    tmp1: Mapped[str] = mapped_column(nullable=True, default="")
    tmp2: Mapped[str] = mapped_column(nullable=True, default="")
    tmp3: Mapped[str] = mapped_column(nullable=True, default="")


class AccountNo_crons_admin(Base):
    __tablename__ = "AccountNo_crons_admin"

    id: Mapped[int] = mapped_column(primary_key=True)
    DateCreated: Mapped[datetime]
    AccountNo: Mapped[str] = mapped_column(nullable=False)
    Description: Mapped[str] = mapped_column(nullable=True, default="")
    status: Mapped[str] = mapped_column(nullable=True, default="")
    cron1: Mapped[bool] = mapped_column(nullable=True, default=0)
    cron2: Mapped[bool] = mapped_column(nullable=True, default=0)
    cron3: Mapped[bool] = mapped_column(nullable=True, default=0)
    cron4: Mapped[bool] = mapped_column(nullable=True, default=0)


class Terms_tbl(Base):
    __tablename__ = "Terms_tbl"

    TermID: Mapped[int] = mapped_column(primary_key=True)
    TermDescription: Mapped[str] = mapped_column(nullable=True, default="")


class Shippers_tbl(Base):
    __tablename__ = "Shippers_tbl"

    ShipperID: Mapped[int] = mapped_column(primary_key=True)
    Shipper: Mapped[str] = mapped_column(nullable=True, default="")


class CreditMemos_tbl(Base):
    __tablename__ = "CreditMemos_tbl"

    CmemoID: Mapped[int] = mapped_column(primary_key=True)
    CmemoNumber: Mapped[str] = mapped_column(nullable=True, default="")
    CmemoDate: Mapped[datetime]


class CreditMemosDetails_tbl(Base):
    __tablename__ = "CreditMemosDetails_tbl"

    LineID: Mapped[int] = mapped_column(primary_key=True)
    CmemoID: Mapped[int] = mapped_column(nullable=True)
    ProductUPC: Mapped[str] = mapped_column(nullable=True, default="")
    ProductDescription: Mapped[str] = mapped_column(nullable=True, default="")
    ProductSKU: Mapped[str] = mapped_column(nullable=True, default="")
    Quantity: Mapped[int] = mapped_column(nullable=True)


class massupdate(Base):
    __tablename__ = "massupdate"

    id: Mapped[int] = mapped_column(primary_key=True)


class Reports(Base):
    __tablename__ = "Reports"

    id: Mapped[int] = mapped_column(primary_key=True)


class QuotationsInProgress(Base):
    __tablename__ = "QuotationsInProgress"

    id: Mapped[int] = mapped_column(primary_key=True)
    StartDate: Mapped[datetime]
    EndDate: Mapped[datetime]
    PauseDate: Mapped[datetime]
    Packer: Mapped[str] = mapped_column(nullable=True, default="")
    Checker: Mapped[str] = mapped_column(nullable=True, default="")
    PauseReason: Mapped[str] = mapped_column(nullable=True, default="")
    SourceDB: Mapped[str] = mapped_column(nullable=True, default="")
    Status: Mapped[str] = mapped_column(nullable=True, default="")
    QuotationNumber: Mapped[str] = mapped_column(nullable=True, default="")
    AccountNo: Mapped[str] = mapped_column(nullable=True, default="")
    SalesRepID: Mapped[int] = mapped_column(nullable=True)
    ProductDescription: Mapped[str] = mapped_column(nullable=True, default="")
    ProductUPC: Mapped[str] = mapped_column(nullable=True, default="")
    ProductSKU: Mapped[str] = mapped_column(nullable=True, default="")
    Qty: Mapped[int] = mapped_column(nullable=True)
    CateID: Mapped[int] = mapped_column(nullable=True)
    SubCateID: Mapped[int] = mapped_column(nullable=True)
    tempField1: Mapped[str] = mapped_column(nullable=True, default="")
    tempField2: Mapped[str] = mapped_column(nullable=True, default="")
    tempField3: Mapped[str] = mapped_column(nullable=True, default="")
    flag1: Mapped[bool] = mapped_column(nullable=True, default=0)
    flag2: Mapped[bool] = mapped_column(nullable=True, default=0)
    flag3: Mapped[bool] = mapped_column(nullable=True, default=0)


class CompanyInfo_tbl(Base):
    __tablename__ = "CompanyInfo_tbl"

    CompanyName: Mapped[str] = mapped_column(primary_key=True)
    Address1: Mapped[str] = mapped_column(nullable=True, default="")
    Address2: Mapped[str] = mapped_column(nullable=True, default="")
    City: Mapped[str] = mapped_column(nullable=True, default="")
    State: Mapped[str] = mapped_column(nullable=True, default="")
    ZipCode: Mapped[str] = mapped_column(nullable=True, default="")
    PhoneNumber: Mapped[str] = mapped_column(nullable=True, default="")
    FaxNumber: Mapped[str] = mapped_column(nullable=True, default="")


class AccountSyncSetting(Base):
    __tablename__ = 'account_sync_settings'
    __table_args__ = (
        Index(
            'ix_account_sync_source_target_db',
            'db_name', 'source_user_id', 'target_user_id',
            unique=True
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment='PK'
    )
    db_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment='Which database this sync applies to'
    )
    source_user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='ID of the source user'
    )
    target_user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='Target user identifier (Employees_tbl.EmployeeID)'
    )
    target_username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment='FirstName from Employees_tbl'
    )
    sync_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment='Whether this account is enabled for sync'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment='When this record was created'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment='When this record was last updated'
    )
