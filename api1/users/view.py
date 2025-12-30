from typing import Any, List, Dict
import re
import random

from sqlalchemy.orm import Session
from starlette_admin import action
from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from starlette.requests import Request

from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import FormValidationError

from starlette_admin import (
    CollectionField,
    ColorField,
    EmailField,
    ExportType,
    IntegerField,
    JSONField,
    ListField,
    StringField,
    DateTimeField,
    TimeField,
    DateField,
    URLField,
    HasOne,
    HasMany,
    IntegerField1,
    EnumField1,
    EnumField,
    FloatField,
    FloatField1,
    FloatField2,
    FloatField3,
    TextAreaField,
    DateField_dig,
    BooleanField,
)
from starlette_admin.fields import FileField


from .model import (
    CheckInvertory,
    Invoices2_tbl,
    InvoicesDetails_tbl,
    Items_tbl,
    ManualInventoryUpdate,
    Manufacturers_tbl,
    OrdersLock,
    PurchaseOrder,
    Reports,
    SubCategories_tbl,
    Categories_tbl,
    Invoices_tbl,
    Quotations_tbl,
    Quotations1_tbl,
    Quotations3_tbl,
    Quotation,
    AdminDBs_admin,
    massupdate,
    shed_admin,
    UploadFile,
)

from .. import engine
from .. import SCW_INDEX
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete


SCW_INDEX -= 1


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
        stmt_select_insert_alias = select(AdminDBs_admin.__table__.columns)
        rows = session.execute(stmt_select_insert_alias).mappings().all()
        ans_list = []
        for i in rows:
            ans_list.append(i["Nick"])
        return ans_list


gen_list = gen_name()
AVAILABLE_USER_TYPES = [
    ("DB1", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]
AVAILABLE_DBs = list()
AVAILABLE_DBs_1 = list()
for i in engine:
    numbdb = i[-1]
    if i == "DB_admin":
        continue

    AVAILABLE_DBs_temp = list()
    AVAILABLE_DBs_temp_1 = list()
    if i != "DB1":
        AVAILABLE_DBs_temp_1.append(i)
        AVAILABLE_DBs_temp_1.append(gen_list[int(numbdb) - 1])
        AVAILABLE_DBs_1.append(tuple(AVAILABLE_DBs_temp_1))
    AVAILABLE_DBs_temp.append(i)
    AVAILABLE_DBs_temp.append(gen_list[int(numbdb) - 1])
    AVAILABLE_DBs.append(tuple(AVAILABLE_DBs_temp))


def gen():
    gen_list = []
    data_list = ["Admin", "Content writer", "Editor", "Regular user"]
    for i in data_list:
        temp_list = []
        WordStack1 = ["A", "B", "C", "D"]
        WordStack2 = ["2", "3", "5", "7"]
        temp_list.append(random.choice(WordStack2))
        temp_list.append(random.choice(WordStack1))

        gen_list.append(tuple(temp_list))
    return gen_list


class Items_tblView(ModelView):
    search_builder = True
    fields = [
        EnumField1(
            "Prodtempl1",
            choices=gen(),
            select2=True,
            identity="prodtempl_db1",
            identity1="items_tbl",
            identity2="prodtempldb1",
            identity3=f"{gen_list[0]} Product Lookup",
            identity4="requirementoptional",
        ),
        EnumField1(
            "Prodtempl2",
            choices=gen(),
            select2=True,
            identity="prodtempl_db2",
            identity1="items_tbl",
            identity2="prodtempldb2",
            identity3=f"{gen_list[1]} Product Lookup",
            identity4="requirementoptional",
        ),
        EnumField1(
            "Prodtempl3",
            choices=gen(),
            select2=True,
            identity="prodtempl_db3",
            identity1="items_tbl",
            identity2="prodtempldb3",
            identity3=f"{gen_list[2]} Product Lookup",
            identity4="requirementoptional",
        ),
        EnumField1(
            "Prodtempl4",
            choices=gen(),
            select2=True,
            identity="prodtempl_db4",
            identity1="items_tbl",
            identity2="prodtempldb4",
            identity3=f"{gen_list[SCW_INDEX]} Product Lookup",
            identity4="requirementoptional",
        ),
        FloatField3(
            "ProductDescription",
            identity3="Product Description",
            identity4="requirement",
        ),
        FloatField2("ProductSKU", identity3="Product SKU", identity4="requirement"),
        FloatField2("ProductUPC", identity3="Product UPC", identity4="requirement"),
        FloatField1(
            "UnitCost1",
            identity="manu_db1",
            identity1="items_tbl",
            identity2="unicost1",
            identity3=f"{gen_list[0]} Cost",
            identity4="requirement",
            identity5="test",
        ),
        FloatField1(
            "UnitCost2",
            identity="manu_db2",
            identity1="items_tbl",
            identity2="unicost2",
            identity3=f"{gen_list[1]} Cost",
            identity4="requirement",
            identity5="test",
        ),
        FloatField1(
            "UnitCost3",
            identity="manu_db3",
            identity1="items_tbl",
            identity2="unicost3",
            identity3=f"{gen_list[2]} Cost",
            identity4="requirement",
            identity5="test",
        ),
        FloatField1(
            "UnitCost4",
            identity="manu_db4",
            identity1="items_tbl",
            identity2="unicost4",
            identity3=f"{gen_list[SCW_INDEX]} Cost",
            identity4="requirement",
            identity5="test",
        ),
        FloatField1(
            "UnitPrice11",
            identity="manu_db1",
            identity1="items_tbl",
            identity2="unitprice1",
            identity3=f"{gen_list[0]} Sales Price",
            identity4="requirement",
            identity5="test",
        ),
        FloatField1(
            "UnitPrice21",
            identity="manu_db2",
            identity1="items_tbl",
            identity2="unitprice2",
            identity3=f"{gen_list[1]} Sales Price",
            identity4="requirement",
            identity5="test",
        ),
        FloatField1(
            "UnitPrice31",
            identity="manu_db3",
            identity1="items_tbl",
            identity2="unitprice3",
            identity3=f"{gen_list[2]} Sales Price",
            identity4="requirement",
            identity5="test",
        ),
        FloatField1(
            "UnitPrice41",
            identity="manu_db4",
            identity1="items_tbl",
            identity2="unitprice4",
            identity3=f"{gen_list[SCW_INDEX]} Sales Price",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "CateID1",
            choices=gen(),
            select2=True,
            identity="categories_db1",
            identity1="items_tbl",
            identity2="test1",
            identity3=f"{gen_list[0]} Category / Subcategory",
            identity4="requirement",
        ),
        EnumField1(
            "CateID2",
            choices=gen(),
            select2=True,
            identity="categories_db2",
            identity1="items_tbl",
            identity2="test2",
            identity3=f"{gen_list[1]} Category / Subcategory",
            identity4="requirement",
        ),
        EnumField1(
            "CateID3",
            choices=gen(),
            select2=True,
            identity="categories_db3",
            identity1="items_tbl",
            identity2="test3",
            identity3=f"{gen_list[2]} Category / Subcategory",
            identity4="requirement",
        ),
        EnumField1(
            "CateID4",
            choices=gen(),
            select2=True,
            identity="categories_db4",
            identity1="items_tbl",
            identity2="test4",
            identity3=f"{gen_list[SCW_INDEX]} Category / Subcategory",
            identity4="requirement",
        ),
        FloatField2(
            "ItemWeight", identity3="Weight", identity4="optional", identity5="test"
        ),
        FloatField2(
            "ItemSize", identity3="Size", identity4="optional", identity5="test"
        ),
        FloatField2(
            "CountInUnit",
            identity3="Count In Unit",
            identity4="optional",
            identity5="test",
        ),
        EnumField1(
            "ManuID1",
            choices=gen(),
            select2=True,
            identity="manu_db1",
            identity1="items_tbl",
            identity2="manutest1",
            identity3=f"{gen_list[0]} Manufacturer",
            identity4="optional",
        ),
        EnumField1(
            "ManuID2",
            choices=gen(),
            select2=True,
            identity="manu_db2",
            identity1="items_tbl",
            identity2="manutest2",
            identity3=f"{gen_list[1]} Manufacturer",
            identity4="optional",
        ),
        EnumField1(
            "ManuID3",
            choices=gen(),
            select2=True,
            identity="manu_db3",
            identity1="items_tbl",
            identity2="manutest3",
            identity3=f"{gen_list[2]} Manufacturer",
            identity4="optional",
        ),
        EnumField1(
            "ManuID4",
            choices=gen(),
            select2=True,
            identity="manu_db4",
            identity1="items_tbl",
            identity2="manutest4",
            identity3=f"{gen_list[SCW_INDEX]} Manufacturer",
            identity4="optional",
        ),
        EnumField1(
            "UnitID11",
            choices=gen(),
            select2=True,
            identity="manu_db1",
            identity1="items_tbl",
            identity2="unitid1",
            identity3=f"{gen_list[0]} Packaging",
            identity4="optional",
            identity5="test",
        ),
        EnumField1(
            "UnitID21",
            choices=gen(),
            select2=True,
            identity="manu_db2",
            identity1="items_tbl",
            identity2="unitid2",
            identity3=f"{gen_list[1]} Packaging",
            identity4="optional",
            identity5="test",
        ),
        EnumField1(
            "UnitID31",
            choices=gen(),
            select2=True,
            identity="manu_db3",
            identity1="items_tbl",
            identity2="unitid3",
            identity3=f"{gen_list[2]} Packaging",
            identity4="optional",
            identity5="test",
        ),
        EnumField1(
            "UnitID41",
            choices=gen(),
            select2=True,
            identity="manu_db4",
            identity1="items_tbl",
            identity2="unitid4",
            identity3=f"{gen_list[SCW_INDEX]} Packaging",
            identity4="optional",
            identity5="test",
        ),
        EnumField1(
            "TaxID11",
            choices=gen(),
            select2=True,
            identity="manu_db1",
            identity1="items_tbl",
            identity2="taxid1",
            identity3=f"{gen_list[0]} Tax",
            identity4="optional",
            identity5="test",
        ),
        EnumField1(
            "TaxID21",
            choices=gen(),
            select2=True,
            identity="manu_db2",
            identity1="items_tbl",
            identity2="taxid2",
            identity3=f"{gen_list[1]} Tax",
            identity4="optional",
            identity5="test",
        ),
        EnumField1(
            "TaxID31",
            choices=gen(),
            select2=True,
            identity="manu_db3",
            identity1="items_tbl",
            identity2="taxid3",
            identity3=f"{gen_list[2]} Tax",
            identity4="optional",
            identity5="test",
        ),
        EnumField1(
            "TaxID41",
            choices=gen(),
            select2=True,
            identity="manu_db4",
            identity1="items_tbl",
            identity2="taxid4",
            identity3=f"{gen_list[SCW_INDEX]} Tax",
            identity4="optional",
            identity5="test",
        ),
    ]
    fields_default_sort = [Items_tbl.ProductID, ("ProductID", False)]

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        errors: Dict[str, str] = {}
        if data["CountInUnit"] and not data["CountInUnit"].isdigit():
            errors["CountInUnit"] = "This is a only digits field"
        if data["CateID1"] is None:
            errors["CateID1"] = "This is a required field"
        if data["CateID2"] is None:
            errors["CateID2"] = "This is a required field"
        if data["CateID3"] is None:
            errors["CateID3"] = "This is a required field"
        if data["CateID4"] is None:
            errors["CateID4"] = "This is a required field"
        if len(data["ProductDescription"]) == 0 or len(data["ProductDescription"]) > 50:
            errors["ProductDescription"] = "Required field, max 50 characters"
        if len(data["ProductSKU"]) == 0 or len(data["ProductSKU"]) > 20:
            errors["ProductSKU"] = "Product SKU Exceeded Maximum Length (20)"
        if data["ProductUPC"] is None or len(data["ProductUPC"]) == 0:
            errors["ProductUPC"] = "This is a required field"
        if data["UnitCost1"] is None:
            errors["UnitCost1"] = "This is a required field"
        if data["UnitCost2"] is None:
            errors["UnitCost2"] = "This is a required field"
        if data["UnitCost3"] is None:
            errors["UnitCost3"] = "This is a required field"
        if data["UnitCost4"] is None:
            errors["UnitCost4"] = "This is a required field"
        if data["UnitPrice11"] is None:
            errors["UnitPrice11"] = "This is a required field"
        if data["UnitPrice21"] is None:
            errors["UnitPrice21"] = "This is a required field"
        if data["UnitPrice31"] is None:
            errors["UnitPrice31"] = "This is a required field"
        if data["UnitPrice41"] is None:
            errors["UnitPrice41"] = "This is a required field"
        if len(errors) > 0:
            raise FormValidationError(errors)
        return await super().validate(request, data)


class Manufacturers_tblView(ModelView):
    fields = [
        StringField(
            "ManuName", label="Manufacturer Name", help_text="Add Manufacturer name"
        ),
        "Items_Manufacturers",
    ]
    fields_default_sort = [Manufacturers_tbl.ManufacturerID, ("ManufacturerID", False)]


class Subcategories_tblView(ModelView):
    fields = [
        StringField(
            "SubCateName",
            label="Subcategory Name",
            help_text="Add name for Subcategory",
        ),
        ColorField(
            "color_code", label="Color code", help_text="choose color for Category"
        ),
        "Items_Subcategories",
    ]
    fields_default_sort = [SubCategories_tbl.SubCateID, ("SubCateID", False)]


class Categories_tblView(ModelView):
    fields = [
        StringField(
            "CategoryName", label="Category Name", help_text="Add Category name"
        ),
        "Subcategories",
        IntegerField(
            "CategoryNo", label="Category Number", help_text="Add Number for Category"
        ),
    ]
    fields_default_sort = [Categories_tbl.CategoryID, ("CategoryID", False)]


class Invoices_tblView(ModelView):
    create_template: str = "create_invoices.html"
    fields = [
        EnumField(
            "choicedb_source",
            choices=AVAILABLE_DBs,
            select2=False,
            identity3="Choose Source DB",
            identity4="requirement",
            identity5="choose1",
        ),
        EnumField1(
            "choicedb_destination",
            choices=gen(),
            select2=True,
            identity1="invoices_tbl",
            identity2="SourceDBcopy",
            identity3="Choose Destination DB",
            identity4="requirement",
            identity5="choose",
        ),
        EnumField1(
            "Account_Number",
            choices=gen(),
            select2=True,
            identity1="accountnumbercopy",
            identity2="accountnumbercopy",
            identity3="Account Number",
            identity4="optional",
            identity5="test",
        ),
        EnumField1(
            "Sales_Rep",
            choices=gen(),
            select2=True,
            identity1="salesrepinvoices",
            identity2="salesrepinvoices",
            identity3="Sales Rep",
            identity4="optional",
            identity5="test",
        ),
        BooleanField(
            "activated_Invoices_tbl",
            label="Activated",
            help_text="Check Box Delivery B (on - UnitPriceC/off - UnitPrice)",
        ),
        FloatField2("invoice", identity3="Insert Invoice number", identity4="optional"),
        FloatField2("queryname", identity3="Query Name", identity4="optional"),
        TextAreaField(
            "QUERY",
            identity3="Insert your QUERY",
            identity4="requirement",
            identity5="query",
        ),
        EnumField1(
            "queryalias",
            choices=gen(),
            select2=True,
            identity="queryalias_admin",
            identity1="invoices_tbl",
            identity2="queryalias1",
            identity3=f"{gen_list[0]} Choose Query",
            identity4="optional",
            identity5="test",
        ),
    ]
    fields_default_sort = [Invoices_tbl.InvoiceID, ("InvoiceID", False)]

    async def validate_load_query(self, request: Request, data: Dict[str, Any]) -> None:
        errors: Dict[str, str] = {}
        if data["queryalias"] == None:
            errors["queryalias"] = "This is a required field"
        if len(errors) > 0:
            raise FormValidationError(errors)
        return await super().validate(request, data)

    async def validate_save_query(self, request: Request, data: Dict[str, Any]) -> None:
        errors: Dict[str, str] = {}
        if len(data["queryname"]) == 0 or len(data["queryname"]) < 3:
            errors["queryname"] = (
                "This is a required field and must contain more than 3 characters"
            )
        if len(data["QUERY"]) == 0:
            errors["QUERY"] = (
                "This is a required field and must contain more than 10 characters"
            )
        if len(data["QUERY"]) > 3000:
            errors["QUERY"] = (
                "Your Query is big. You must contain no more than 3000 characters"
            )
        if len(errors) > 0:
            raise FormValidationError(errors)
        return await super().validate(request, data)

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        errors: Dict[str, str] = {}
        if data["invoice"] and not data["invoice"].isdigit():
            errors["invoice"] = "This is a only digits field"
        if (
            len(data["invoice"]) == 0
            and data["Account_Number"] == None
            and data["Sales_Rep"] == None
        ):
            errors["invoice"] = (
                "You must fill Account Number and Sales_Rep or Invoice number fields"
            )
            errors["Sales_Rep"] = (
                "You must fill Account Number and Sales_Rep or Invoice number fields"
            )
            errors["Account_Number"] = (
                "You must fill Account Number and Sales_Rep or Invoice number fields"
            )
        if len(data["QUERY"]) == 0 or len(data["QUERY"]) < 9:
            errors["QUERY"] = "This is a required field"
        if data["choicedb_source"] == None:
            errors["choicedb_source"] = "This is a required field"

        if data["choicedb_destination"] == None:
            errors["choicedb_destination"] = "This is a required field"

        if re.search(r"\bDROP\b", data["QUERY"]) or re.search(
            r"\bdrop\b", data["QUERY"]
        ):
            errors["QUERY"] = "This command is impossible in this system"
        if re.search(r"\bINSERT\b", data["QUERY"]) or re.search(
            r"\binsert\b", data["QUERY"]
        ):
            errors["QUERY"] = "This command is impossible in this system"

        if re.search(r"\bUPDATE\b", data["QUERY"]) or re.search(
            r"\bupdate\b", data["QUERY"]
        ):
            errors["QUERY"] = "This command is impossible in this system"

        if re.search(r"\blineid\b", data["QUERY"].lower()) == None:
            errors["QUERY"] = "Use this query with parameter 'LineId'"
        if re.search(r"\bqty\b", data["QUERY"].lower()) == None:
            errors["QUERY"] = "Use this query with parameter 'QTY'"
        if len(errors) > 0:
            raise FormValidationError(errors)
        return await super().validate(request, data)


class QuotationView(ModelView):
    create_template: str = ("create_quotation.html",)
    view_table = (False,)
    fields = [
        DateField_dig("DateCreate", label="Date"),
        TextAreaField("QuotationNumber", label="Quotation"),
        TextAreaField("InvoiceNumber", label="Invoice"),
        TextAreaField("BusinessName", label="Customer"),
        TextAreaField("SalesRepresentative", label="Sales Rep"),
        TextAreaField("Status", label="Status"),
    ]
    fields_default_sort = [Quotation.id, ("id", False)]


class Quotations_tbl_createView(ModelView):
    create_template: str = "create_new_quotation.html"
    view_field: bool = True
    fields = [
        EnumField1(
            "SourceDB",
            choices=gen(),
            select2=True,
            identity1="quotations1_tbl",
            identity2="SourceDB",
            identity3="Select DB",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "BusinessName",
            choices=gen(),
            select2=True,
            identity1="quotations1_tbl",
            identity2="businessnamequotation",
            identity3="Business Name",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "AccountNo",
            choices=gen(),
            select2=True,
            identity1="quotations1_tbl",
            identity2="accountnoquotation",
            identity3="Account Number",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "ProductDescription",
            choices=gen(),
            select2=True,
            identity1="quotations1_tbl",
            identity2="productdescriptionquotation",
            identity3="Product Description",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "SKU",
            choices=gen(),
            select2=True,
            identity1="quotations1_tbl",
            identity2="productskuquotation",
            identity3="SKU",
            identity4="requirement",
            identity5="test",
        ),
        FloatField2(
            "QTY",
            identity2="qtyquotation",
            identity3="QTY",
            identity4="requirement",
        ),
        FloatField1(
            "Price",
            identity2="pricequotation",
            identity3="Price",
            identity4="requirement",
        ),
        FloatField1(
            "Total",
            identity2="totalquotation",
            identity3="Total",
            identity4="requirement",
        ),
    ]

    fields_default_sort = [Quotations1_tbl.id, ("id", False)]

    async def validate_new_quotation(
        self, request: Request, data: Dict[str, Any]
    ) -> None:
        errors: Dict[str, str] = {}
        if data["QTY"] is not None and not data["QTY"].isdigit():
            errors["QTY"] = "This is a only digits field"
        if data["QTY"] is not None and data["QTY"] <= 0:
            errors["QTY"] = "Enter correctly QTY"
        if data["Price"] and not data["Price"].isdigit():
            errors["Price"] = "This is a only digits field"
        if len(errors) > 0:
            raise FormValidationError(errors)
        return await super().validate(request, data)

class ListInvoicesView(ModelView):
    create_template: str = "list_all_invoices.html"
    fields = [
        EnumField(
            "choicedb_source",
            choices=AVAILABLE_DBs,
            select2=False,
            identity3="Choose Source DB Invoices",
            identity4="optional",
            identity5="choose",
            identity6="no",
        ),
        DateField_dig("InvoiceDate", label="Date Created"),
        TextAreaField("InvoiceNumber", label="Invoice Number"),
        TextAreaField("AccountNo", label="Account No"),
        TextAreaField("Customer", label="Customer"),
        FloatField1("InvoiceTotal", label="Invoice Total"),
        FloatField1("Balance", label="Balance"),
        TextAreaField("FirstName", label="Sales Rep"),
        TextAreaField("TermDescription", label="Payment Terms"),
        TextAreaField("Shipper", label="Shipper"),
        TextAreaField("TrackingNo", label="Tracking number"),
        TextAreaField("ShippingCost", label="Shipping Cost"),
        TextAreaField("Notes", label="Notes"),
    ]

    fields_default_sort = [Invoices2_tbl.InvoiceID, ("InvoiceID", False)]


class Quotations2_tbl_createView(ModelView):
    create_template: str = "list_all_quotation.html"
    fields = [
        EnumField(
            "choicedb_source",
            choices=AVAILABLE_DBs,
            select2=False,
            identity3="Choose Source DB Quotations",
            identity4="optional",
            identity5="choose",
            identity6="no",
        ),
        DateField_dig("QuotationDate", label="Date Created"),
        TextAreaField("QuotationNumber", label="Quotation Number"),
        TextAreaField("AccountNo", label="Account No"),
        TextAreaField("BusinessName", label="Business Name"),
        TextAreaField("Total", label="Total"),
        # TextAreaField("DBname", label="DB name"),
        TextAreaField("ProfitMargin", label="Profit Margin"),
        TextAreaField("FirstName", label="Sales Rep"),
        TextAreaField("StatusQuotation", label="Status"),
    ]

    fields_default_sort = [Quotations1_tbl.id, ("id", False)]

    async def validate_new_quotation(
        self, request: Request, data: Dict[str, Any]
    ) -> None:
        errors: Dict[str, str] = {}
        if data["QTY"] is not None and not data["QTY"].isdigit():
            errors["QTY"] = "This is a only digits field"
        if data["QTY"] is not None and data["QTY"] <= 0:
            errors["QTY"] = "Enter correctly QTY"
        if data["Price"] and not data["Price"].isdigit():
            errors["Price"] = "This is a only digits field"
        if len(errors) > 0:
            raise FormValidationError(errors)
        return await super().validate(request, data)


class Quotations3_tbl_createView(ModelView):
    create_template: str = "create_new_quotation_edit.html"
    view_field: bool = True
    fields = [
        EnumField1(
            "SourceDB",
            choices=gen(),
            select2=True,
            identity1="quotations3_tbl",
            identity2="SourceDB",
            identity3="Select DB",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "BusinessName",
            choices=gen(),
            select2=True,
            identity1="quotations3_tbl",
            identity2="businessnamequotation",
            identity3="Business Name",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "AccountNo",
            choices=gen(),
            select2=True,
            identity1="quotations3_tbl",
            identity2="accountnoquotation",
            identity3="Account Number",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "ProductDescription",
            choices=gen(),
            select2=True,
            identity1="quotations3_tbl",
            identity2="productdescriptionquotation",
            identity3="Product Description",
            identity4="requirement",
            identity5="test",
            label="Product Description",
        ),
        EnumField1(
            "ProductSKU",
            choices=gen(),
            select2=True,
            identity1="quotations3_tbl",
            identity2="productskuquotation",
            identity3="SKU",
            identity4="requirement",
            identity5="test",
            label="SKU",
        ),
        FloatField2(
            "Qty",
            identity2="qtyquotation",
            identity3="QTY",
            identity4="requirement",
            label="QTY",
        ),
        FloatField1(
            "UnitPrice",
            identity2="pricequotation",
            identity3="Price",
            identity4="requirement",
            label="Price",
        ),
        FloatField1(
            "Total",
            identity2="totalquotation",
            identity3="Total",
            identity4="requirement",
            label="Total",
        ),
    ]

    fields_default_sort = [Quotations3_tbl.LineID, ("id", False)]

    async def validate_new_quotation(
        self, request: Request, data: Dict[str, Any]
    ) -> None:
        errors: Dict[str, str] = {}
        if len(errors) > 0:
            raise FormValidationError(errors)
        return await super().validate(request, data)


class Quotationsdetails1_tbl_editView(ModelView):
    create_template: str = "edit_quotation.html"
    view_field: bool = True
    fields = [
        TextAreaField("ProductDescription", label="Description"),
        TextAreaField("ProductSKU", label="SKU"),
        EnumField1(
            "ProductDescription",
            choices=gen(),
            select2=True,
            identity1="quotations3_tbl",
            identity2="productdescriptionquotationedit",
            identity3="Product Description",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "SKU",
            choices=gen(),
            select2=True,
            identity1="quotations3_tbl",
            identity2="productskuquotationedit",
            identity3="SKU",
            identity4="requirement",
            identity5="test",
        ),
        FloatField2(
            "Qty",
            identity2="qtyquotation",
            identity3="Qty",
            identity4="requirement",
        ),
        FloatField1(
            "UnitPrice",
            identity2="pricequotation",
            identity3="Unit Price",
            identity4="requirement",
            label="Price",
        ),
    ]

    fields_default_sort = [Quotations1_tbl.id, ("id", False)]


class InvoicesDetailsView(ModelView):
    create_template: str = "invoices_details.html"
    view_field: bool = True
    fields = [
        TextAreaField("ProductDescription", label="Description"),
        TextAreaField("QtyShipped", label="Shipped Quantity"),
        TextAreaField("UnitPrice", label="Unit Price"),
        TextAreaField("OriginalPrice", label="Original Price"),
        TextAreaField("Total", label="Total"),
    ]

    fields_default_sort = [InvoicesDetails_tbl.LineID, ("id", False)]

    async def validate_new_quotation(
        self, request: Request, data: Dict[str, Any]
    ) -> None:
        errors: Dict[str, str] = {}
        if len(errors) > 0:
            raise FormValidationError(errors)
        return await super().validate(request, data)


class FileView(ModelView):
    fields = [
        "id",
        TextAreaField("QuotationNumber", label="Uploaded_file_1"),
        TextAreaField("QuotationNumber", label="Uploaded_file_2"),
        TextAreaField("QuotationNumber", label="Uploaded_file_3"),
    ]
    fields_default_sort = [UploadFile.id, ("id", False)]


class Reports_createView(ModelView):
    fields = [
        "id",
        DateField(
            "DateFrom",
            label="Date From",
            identity1="datefrom",
            identity2="datefrom",
            identity3="Date From",
            identity4="requirement",
        ),
        DateField(
            "DateTo",
            label="Date To",
            identity1="dateto",
            identity2="dateto",
            identity3="Date To",
            identity4="requirement",
        ),
        FloatField2(
            "ProductDescription",
            label="ProductDescription",
            identity2="productdescriptionmanual",
            identity3="Product Description",
            # identity4="requirement",
            identity5="test",
        ),
        FloatField2(
            "SKU",
            label="SKU",
            identity2="productskumanual",
            identity3="SKU",
            # identity4="requirement",
            identity5="test",
        ),
        FloatField2(
            "ProductUPC",
            label="UPC",
            identity2="productupcmanual",
            identity3="UPC",
            # identity4="requirement",
            identity5="test",
        ),
    ]
    fields_default_sort = [Reports.id, ("id", False)]


class ManualInventoryUpdateView(ModelView):
    fields = [
        EnumField1(
            "ProductDescription",
            choices=gen(),
            select2=True,
            identity1="manualinventoryupdate",
            identity2="productdescriptionmanual",
            identity3="Product Description",
            identity4="requirement",
            identity5="test",
        ),
        EnumField1(
            "SKU",
            choices=gen(),
            select2=True,
            identity1="manualinventoryupdate",
            identity2="productskumanual",
            identity3="SKU",
            identity4="requirement",
            identity5="test",
        ),
        FloatField2(
            "ProductUPC",
            label="UPC",
            identity2="productupcmanual",
            identity3="UPC",
            identity4="requirement",
            identity5="test",
        ),
        FloatField1(
            "Qty",
            identity2="qtymanual",
            identity3="Qty",
            label="Price",
        ),
        FloatField2(
            "newQty",
            identity2="newqtymanual",
            identity3="New Qty",
        ),
    ]
    fields_default_sort = [ManualInventoryUpdate.id, ("id", False)]


class OrdersLockView(ModelView):
    fields = [
        FloatField2(
            "orderslock",
            identity2="orderslock",
            identity3="Please Scan Quotation Number",
        ),
    ]
    fields_default_sort = [OrdersLock.id, ("id", False)]


class SettingsView(ModelView):
    fields = []
    fields_default_sort = []
    create_template: str = "settings.html"


class PurchaseOrderView(ModelView):
    fields = []
    fields_default_sort = [PurchaseOrder.id, ("id", False)]


class massupdateView(ModelView):
    fields = []
    fields_default_sort = [massupdate.id, ("id", False)]
