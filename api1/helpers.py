import json
import os
from typing import Any, Callable, Dict, Iterable, Type

from api1.constants import CONFIG_PATH, DEFAULT_ACTIVE_TIME_RANGE

from starlette.datastructures import UploadFile as StarletteUploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request


class UploadFile(StarletteUploadFile):
    @classmethod
    def __get_validators__(cls: Type["UploadFile"]) -> Iterable[Callable[..., Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: Type["UploadFile"], v: Any) -> Any:
        if not isinstance(v, StarletteUploadFile):
            raise ValueError(f"Expected UploadFile, received: {type(v)}")
        return v

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update({"type": "string", "format": "binary"})


def get_assets(path: str):
    cur_dir = os.path.dirname(__file__)
    return os.path.join(cur_dir, "../assets/", path)


def save_time_range_config(cfg: dict[str, int]) -> None:
    """
    Save the given config dict to config/time_range.json with indentation for readability.
    """
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def load_time_range_config() -> dict[str, int]:
    """
    Load the config/time_range.json file; if it doesn't exist, create it with {"months": 3}.

    Active time range limit specifies the retrospective window for database queries
    e.g., a value of 6 months retrieves all records from the past six months.
    """
    if not CONFIG_PATH.exists():
        save_time_range_config({"months": DEFAULT_ACTIVE_TIME_RANGE})
    return json.loads(CONFIG_PATH.read_text())


def fetch_user_menu_and_default(username: str):
    """
    Return (menu_key, accessmenu_list, matches_description) or None if user not found.
    - menu_key: the 'menu' column (e.g. "invoices2_tbl") corresponding to the stored description.
    - accessmenu_list: user.accessmenu.split("/") – list of allowed menu keys.
    - matches_description: True if we successfully found a row in admin_menu_list by description.
    """
    
    from api1.users.model import AdminUserProject_admin
    from api1 import engine
    from api1.users.model import admin_menu_list

    try:
        with Session(engine["DB_admin"]) as session:
            user = (
                session
                .query(AdminUserProject_admin)
                .filter_by(username=username)
                .first()
            )

            if not user:
                return None

            # accessmenu holds descriptions, e.g. "Items/Invoices/Settings"
            raw_access = user.accessmenu or ""
            accessmenu_list = raw_access.split("/") if raw_access else []

            stored_desc = user.default_home_page  # e.g. "Invoices" or None
            if not stored_desc:
                # No default description set
                return (None, accessmenu_list, False)

            # Check if stored_desc is one of the allowed descriptions
            if stored_desc not in accessmenu_list:
                return (None, accessmenu_list, False)
                

            # Now find in admin_menu_list the row where description == stored_desc
            row = (
                session
                .query(admin_menu_list)
                .filter(admin_menu_list.description == stored_desc)
                .first()
            )
            if not row:
                # Description not found in admin_menu_list
                raise KeyError("Not row")
                return (None, accessmenu_list, False)

            # Return (menu_key = row.menu, list of descriptions, True)
            return (row.menu, accessmenu_list, True)

    except SQLAlchemyError:
        return None


def get_client_ip(request: Request) -> str:
    return request.client.host
