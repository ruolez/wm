from typing import Any, List, Dict

from sqlalchemy.orm import Session
from starlette_admin import action
from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from starlette_admin import EnumField, ExportType, StringField, IntegerField
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
    URLField,
)


from .model import Items_tbl, Manufacturers_tbl


AVAILABLE_USER_TYPES = [
    ("admin", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]


class Items_tblView(ModelView):
    fields = [
        IntegerField("ProductID", label="Product ID", help_text="Product ID"),
        IntegerField("CateID", label="Category ID", help_text="Add Category ID"),
        IntegerField(
            "SubCateID", label="SubCategory ID", help_text="Add SubCategory ID"
        ),
        StringField(
            "ProductDescription",
            label="ProductDescription ID",
            help_text="Add SubCategory ID",
        ),
        StringField(
            "ProductSKU", label="ProductSKU ID", help_text="Add SubCategory ID"
        ),
        StringField(
            "ProductUPC", label="ProductUPC ID", help_text="Add SubCategory ID"
        ),
        IntegerField("UnitCost", label="UnitCost ID", help_text="Add SubCategory ID"),
    ]
    fields_default_sort = [Items_tbl.ProductID, ("ProductID", False)]





class Manufacturers_tblView(ModelView):
    fields = [
        IntegerField(
            "ManufacturerID",
            label="Manufacturer ID",
            help_text="Add ID for Manufacturer",
        ),
        StringField(
            "ManuName", label="Manufacturer Name", help_text="Add Manufacturer name"
        ),
    ]
    fields_default_sort = [Manufacturers_tbl.ManufacturerID, ("ManufacturerID", False)]









