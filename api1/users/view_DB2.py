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



from .model_DB2 import Categories_db2_tbl

AVAILABLE_USER_TYPES = [
    ("admin", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]


















