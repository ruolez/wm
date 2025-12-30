import json
from json import JSONDecodeError
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Type, Union
import os
import urllib.parse
import pandas as pd
import aiofiles
import base64
import math
from api1.api_v2.api import send_invoice_email
import httpx
import copy
import datetime
from urllib.parse import urlsplit, parse_qsl
from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from starlette.applications import Starlette
from starlette.datastructures import FormData
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.status import (
    HTTP_303_SEE_OTHER,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from starlette.templating import Jinja2Templates
from starlette_admin._types import RequestAction
from starlette_admin.auth import AuthMiddleware, AuthProvider
from starlette_admin.exceptions import ActionFailed, FormValidationError, LoginFailed
from starlette_admin.helpers import (
    get_file_icon,
    DB_MAPPING,
    generate_unique_quotation_number_simple,
    generate_unique_quotation_number_with_prefix,
)
from starlette_admin.i18n import (
    I18nConfig,
    LocaleMiddleware,
    get_locale,
    get_locale_display_name,
    gettext,
    ngettext,
)
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.views import BaseModelView, BaseView, CustomView, DropDown, Link
from api1 import (
    abs_path,
    engine,
    engine_nick,
    engine_name_db,
    X_TOKEN,
    engine_db_nick_name,
    engine_name_nick,
)
from sqlalchemy.orm import Session
from sqlalchemy import exc as exc_sqlalchemy
from sqlalchemy import (
    Column,
    String,
    cast,
    case,
    Date,
    extract,
    func,
    inspect,
    or_,
    and_,
    not_,
    true,
    false,
    select,
    insert,
    update,
    join,
    outerjoin,
    delete,
    text,
)
from api1.config import sr
from api1.users.model import (
    AccountNo_crons_admin,
    AdminDBs_admin,
    AuditLog,
    BinLocations_tbl,
    CompanyInfo_tbl,
    Inventory,
    Items_BinLocations,
    ManualInventoryUpdate,
    OrderDetails,
    Orders,
    PurchaseOrder,
    PurchaseOrders_tbl,
    PurchaseOrdersDetails_tbl,
    Quotation,
    QuotationDetails,
    Items_tbl,
    Quotations_tbl,
    QuotationsDetails_tbl,
    Employees_tbl,
    QuotationsInProgress,
    QuotationsStatus,
    Shippers_tbl,
    Suppliers_tbl,
    Terms_tbl,
    Tracking,
    admin_query,
    Invoices_tbl,
    InvoicesDetails_tbl,
    QuotationsTemp,
    Customers_tbl,
    Units_tbl,
    admin_menu,
    admin_menu_list,
    AdminUserProject_admin,
    Quotationsdetails1_tbl,
    pick_list_products,
    pick_lists,
)
from api1.pdf import create_invoice_pdf, create_pdf_1, get_bin_locations
from symbol import lambdef


ch_lis = ["Standard", "DeliveryB"]

list_ship = [
    "shipping",
    "SIMPINSUR1",
    "ship",
    "shipment",
    "shipping",
    "simpinsur",
]


def pd_req(query: str, db: str, error=None):
    df = pd.read_sql(query, engine[db])
    answ_invoice = df.to_dict("records")
    return answ_invoice


def SEARCH_IN_DICT_VALUE_RETURN_KEY(dict_data, value):
    for i in dict_data.keys():
        if value == dict_data[i]:
            return i


def mod_value(val):
    if isinstance(val, str):
        val = val.replace("'", "''")
    if (isinstance(val, str) and not val) or (isinstance(val, list) and not val):
        return "''"
    elif val == None:
        return "NULL"
    elif isinstance(val, float) and math.isnan(float(val)):
        return 0.0
    elif val == False:
        return 0
    elif val == True:
        return 1
    elif isinstance(val, int) or isinstance(val, float):
        return val
    else:
        return f"'{val}'"


def WORD_MOD(word):
    for line in "<>=!+#:().,&*%-~|`_":
        word = word.replace(line, "")
    return word

def menu(request: Request):
    try:
        user_account = request.state.user["name"].strip().lower()
    except AttributeError:
        return ""
    with Session(engine["DB_admin"]) as session:
        AVAILABLE_Menu_dict_rev = dict()
        stmt_select_insert_alias = select(admin_menu_list.__table__.columns)
        rows = session.execute(stmt_select_insert_alias).mappings().all()
        for i in rows:
            AVAILABLE_Menu_dict_rev[i["description"]] = i["menu"]
        stmt_menu = select(AdminUserProject_admin.__table__.columns).filter_by(
            username=user_account
        )
        rows_menu = session.execute(stmt_menu).mappings().all()
    menu_description = rows_menu[0]["accessmenu"].split("/")
    menu = [AVAILABLE_Menu_dict_rev[i] for i in menu_description]
    return menu


def checking_str(val):
    if type(val) == bool:
        return "bool"
    dType = "str"
    try:
        float(val)
        dType = "float"
        if str(int(val)) == str(val):
            dType = "int"
    except:
        pass
    return dType


def SPLIT_LIST_TO_LISTS_1(lst, n):
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def SPLIT_LIST_TO_LISTS_2(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def SPLIT_LIST_TO_LISTS_3(lst, n):
    for i in lst:
        yield i


def check_none(dict_obj: dict[str:Any]) -> bool:
    for i in dict_obj:
        if dict_obj[i] != None:
            return False
    return True


def check_token(request: Request):
    if "x-token" not in request.headers:
        return False
    if request.headers["x-token"] != X_TOKEN:
        return False


def checkcomituser(statususer):
    if "commiteruser" in statususer.split("/"):
        return 1
    else:
        return 0


class BaseAdmin:
    def __init__(
        self,
        title: str = _("Admin"),
        base_url: str = "/admin",
        route_name: str = "admin",
        logo_url: Optional[str] = None,
        login_logo_url: Optional[str] = None,
        templates_dir: str = "templates",
        statics_dir: Optional[str] = None,
        index_view: Optional[CustomView] = None,
        auth_provider: Optional[AuthProvider] = None,
        middlewares: Optional[Sequence[Middleware]] = None,
        debug: bool = False,
        i18n_config: Optional[I18nConfig] = None,
    ):
        self.title = title
        self.base_url = base_url
        self.route_name = route_name
        self.logo_url = logo_url
        self.login_logo_url = login_logo_url
        self.templates_dir = templates_dir
        self.statics_dir = statics_dir
        self.auth_provider = auth_provider
        self.middlewares = middlewares
        self.index_view = (
            index_view
            if (index_view is not None)
            else CustomView("", add_to_menu=False)
        )
        self._views: List[BaseView] = []
        self._models: List[BaseModelView] = []
        self.routes: List[Union[Route, Mount]] = []
        self.debug = debug
        self.i18n_config = i18n_config
        self.init_routes_front()
        self._setup_templates()
        self.init_locale()
        self.init_auth()
        self.init_routes()
        request: Request = None

    def add_view(self, view: Union[Type[BaseView], BaseView]) -> None:
        view_instance = view if isinstance(view, BaseView) else view()
        self._views.append(view_instance)
        self.setup_view(view_instance)

    def add_view_no_view(self, view: Union[Type[BaseView], BaseView]) -> None:
        view_instance = view if isinstance(view, BaseView) else view()
        self.setup_view(view_instance)

    def custom_render_js(self, request: Request) -> Optional[str]:
        return None

    def init_locale(self) -> None:
        if self.i18n_config is not None:
            try:
                import babel  # noqa
            except ImportError as err:
                raise ImportError(
                    "'babel' package is required to use i18n features."
                    "Install it with `pip install starlette-admin[i18n]`"
                ) from err
            self.middlewares = (
                [] if self.middlewares is None else list(self.middlewares)
            )
            self.middlewares.insert(
                0, Middleware(LocaleMiddleware, i18n_config=self.i18n_config)
            )

    def init_auth(self) -> None:
        if self.auth_provider is not None:
            self.middlewares = (
                [] if self.middlewares is None else list(self.middlewares)
            )
            self.middlewares.append(
                Middleware(AuthMiddleware, provider=self.auth_provider)
            )
            self.routes.extend(
                [
                    Route(
                        self.auth_provider.login_path,
                        self._render_login,
                        methods=["GET", "POST"],
                        name="login",
                    ),
                    Route(
                        self.auth_provider.logout_path,
                        self._render_logout,
                        methods=["GET"],
                        name="logout",
                    ),
                ]
            )

    def init_routes_front(self) -> None:
        self.routes.extend(
            [
                Route(
                    "/users",
                    self.users,
                    methods=["GET", "POST"],
                    name="users",
                ),
                Route(
                    "/checkactivequotations",
                    self.checkactivequotations,
                    methods=["GET", "POST"],
                    name="checkactivequotations",
                ),
                Route(
                    "/checkprogress",
                    self.checkprogress,
                    methods=["GET", "POST"],
                    name="checkprogress",
                ),
                Route(
                    "/items_all",
                    self.items_all,
                    methods=["GET", "POST"],
                    name="items_all",
                ),
                Route(
                    "/wl1",
                    self.wl1,
                    methods=["GET", "POST"],
                    name="wl1",
                ),
                Route(
                    "/wl2",
                    self.wl2,
                    methods=["GET", "POST"],
                    name="wl2",
                ),
            ]
        )
        return "ok"

    def init_routes(self) -> None:
        statics = StaticFiles(directory=self.statics_dir, packages=["starlette_admin"])
        self.routes.extend(
            [
                Mount("/statics", app=statics, name="statics"),
                Route(
                    self.index_view.path,
                    self._render_custom_view(self.index_view),
                    methods=self.index_view.methods,
                    name="index",
                ),
                Route(
                    "/api1/{identity}",
                    self._render_api,
                    methods=["GET"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/test1",
                    self.test_api1,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/test2",
                    self.test_api2,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/test3",
                    self.test_api3,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/test4",
                    self.test_api4,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/manutest1",
                    self.manutest1,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/manutest2",
                    self.manutest2,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/manutest3",
                    self.manutest3,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/unitid1",
                    self.unitid1,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/unitid2",
                    self.unitid2,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/unitid3",
                    self.unitid3,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/unitid4",
                    self.unitid4,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/taxid1",
                    self.taxid1,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/taxid2",
                    self.taxid2,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/taxid3",
                    self.taxid3,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/taxid4",
                    self.taxid4,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/prodtempldb1",
                    self.prodtempldb1,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/prodtempldb2",
                    self.prodtempldb2,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/prodtempldb3",
                    self.prodtempldb3,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/prodtempldb4",
                    self.prodtempldb4,
                    methods=["GET", "POST"],
                    name="api",
                ),
                Route(
                    "/api1/{identity}/action",
                    self.handle_action,
                    methods=["GET", "POST"],
                    name="action",
                ),
                Route(
                    "/{identity}/detail/{pk}",
                    self._render_detail,
                    methods=["GET"],
                    name="detail",
                ),
                Route(
                    "/{identity}/create_quotation_list",
                    self.create_quotation_list,
                    methods=["GET", "POST"],
                    name="create_quotation_list",
                ),
                Route(
                    "/{identity}/edit/{pk}",
                    self._render_edit1,
                    methods=["GET", "POST"],
                    name="edit",
                ),
                Route(
                    "/{identity}/create_invoice",
                    self._invoice_create,
                    methods=["GET", "POST"],
                    name="create_invoice",
                ),
                Route(
                    "/api1/{identity}/accountnumbercopy",
                    self.accountnumbercopy,
                    methods=["GET", "POST"],
                    name="accountnumbercopy",
                ),
                Route(
                    "/api1/{identity}/salesrepinvoices",
                    self.salesrepinvoices,
                    methods=["GET", "POST"],
                    name="salesrepinvoices",
                ),
                Route(
                    "/api1/{identity}/choicedbdestination",
                    self.choicedbdestination,
                    methods=["GET", "POST"],
                    name="choicedbdestination",
                ),
                Route(
                    "/api1/{identity}/choicedbdestination1",
                    self.choicedbdestination1,
                    methods=["GET", "POST"],
                    name="choicedbdestination1",
                ),
                Route(
                    "/api1/{identity}/queryalias1",
                    self.queryalias1,
                    methods=["GET", "POST"],
                    name="queryalias1",
                ),
                Route(
                    "/{identity}/quotation_update",
                    self.quotation_update,
                    methods=["GET", "POST"],
                    name="quotation_update",
                ),
                Route(
                    "/{identity}/quotation_return",
                    self.quotation_return,
                    methods=["GET", "POST"],
                    name="quotation_return",
                ),
                Route(
                    "/{identity}/new_quotation_edit",
                    self.new_quotation_edit,
                    methods=["GET", "POST"],
                    name="new_quotation_edit",
                ),
                Route(
                    "/{identity}/new_quotation_delete",
                    self.new_quotation_delete,
                    methods=["GET", "POST"],
                    name="new_quotation_delete",
                ),
                Route(
                    "/{identity}/new_quotation_edit_delete",
                    self.new_quotation_edit_delete,
                    methods=["GET", "POST"],
                    name="new_quotation_edit_delete",
                ),
                Route(
                    "/api1/{identity}/view_invoice",
                    self.view_invoice,
                    methods=["GET"],
                    name="view_invoice",
                ),
                Route(
                    "/{identity}/list_quotation",
                    self.list_quotation,
                    methods=["GET", "POST"],
                    name="list_quotation",
                ),
                Route(
                    "/{identity}/delete_quotation",
                    self.delete_quotation,
                    methods=["GET", "POST"],
                    name="delete_quotation",
                ),
                Route(
                    "/{identity}/delete_quotation_details",
                    self.delete_quotation_details,
                    methods=["GET", "POST"],
                    name="delete_quotation_details",
                ),
                Route(
                    "/{identity}/print_quotation",
                    self.print_quotation,
                    methods=["GET", "POST"],
                    name="print_quotation",
                ),
                Route(
                    "/{identity}/upload_files",
                    self.upload_files,
                    methods=["GET", "POST"],
                    name="upload_files",
                ),
                Route(
                    "/{identity}/view_edit_quotation",
                    self.view_edit_quotation,
                    methods=["GET", "POST"],
                    name="view_edit_quotation",
                ),
                Route(
                    "/{identity}/add_quotation",
                    self.add_quotation,
                    methods=["GET", "POST"],
                    name="add_quotation",
                ),
                Route(
                    "/{identity}/checkinvertory",
                    self.checkinvertory,
                    methods=["GET", "POST"],
                    name="checkinvertory",
                ),
                Route(
                    "/{identity}/errorcheckinvertory",
                    self.errorcheckinvertory,
                    methods=["GET", "POST"],
                    name="errorcheckinvertory",
                ),
                Route(
                    "/{identity}/update_add_quotation",
                    self.update_add_quotation,
                    methods=["GET", "POST"],
                    name="update_add_quotation",
                ),
                Route(
                    "/{identity}/update_quotation_details",
                    self.update_quotation_details,
                    methods=["GET", "POST"],
                    name="update_quotation_details",
                ),
                Route(
                    "/{identity}/edit_quotation",
                    self.edit_quotation,
                    methods=["GET", "POST"],
                    name="edit_quotation",
                ),
                Route(
                    "/api1/{identity}/businessnamequotation",
                    self.businessnamequotation,
                    methods=["GET", "POST"],
                    name="businessnamequotation",
                ),
                Route(
                    "/api1/{identity}/accountnoquotation",
                    self.accountnoquotation,
                    methods=["GET", "POST"],
                    name="accountnoquotation",
                ),
                Route(
                    "/api1/{identity}/SourceDB",
                    self.SourceDB,
                    methods=["GET", "POST"],
                    name="SourceDB",
                ),
                Route(
                    "/api1/{identity}/SourceDBcopy",
                    self.SourceDBcopy,
                    methods=["GET", "POST"],
                    name="SourceDBcopy",
                ),
                Route(
                    "/api1/{identity}/productdescriptionquotation",
                    self.productdescriptionquotation,
                    methods=["GET", "POST"],
                    name="productdescriptionquotation",
                ),
                Route(
                    "/api1/{identity}/productdescriptionquotationedit",
                    self.productdescriptionquotationedit,
                    methods=["GET", "POST"],
                    name="productdescriptionquotationedit",
                ),
                Route(
                    "/api1/{identity}/productskuquotation",
                    self.productskuquotation,
                    methods=["GET", "POST"],
                    name="productskuquotation",
                ),
                Route(
                    "/api1/{identity}/productskuquotationedit",
                    self.productskuquotationedit,
                    methods=["GET", "POST"],
                    name="productskuquotationedit",
                ),
                Route(
                    "/api1/{identity}/productdescriptionmanual",
                    self.productdescriptionmanual,
                    methods=["GET", "POST"],
                    name="productdescriptionmanual",
                ),
                Route(
                    "/api1/{identity}/productskumanual",
                    self.productskumanual,
                    methods=["GET", "POST"],
                    name="productskumanual",
                ),
                Route(
                    "/{identity}",
                    self._render_create1,
                    methods=["GET", "POST"],
                    name="list",
                ),
                Route(
                    "/api1/{identity}/browseitems",
                    self.browseitems,
                    methods=["GET", "POST"],
                    name="browseitems",
                ),
                Route(
                    "/api1/{identity}/browseitemsone",
                    self.browseitemsone,
                    methods=["GET", "POST"],
                    name="browseitemsone",
                ),
                Route(
                    "/api1/{identity}/createquoatallinfo",
                    self.createquoatallinfo,
                    methods=["GET", "POST"],
                    name="createquoatallinfo",
                ),
                Route(
                    "/api1/{identity}/getbusinessinfo",
                    self.getbusinessinfo,
                    methods=["GET", "POST"],
                    name="getbusinessinfo",
                ),
                Route(
                    "/api1/{identity}/savequotation",
                    self.savequotation,
                    methods=["GET", "POST"],
                    name="savequotation",
                ),
                Route(
                    "/api1/{identity}/removeReadOnly",
                    self.removeReadOnly,
                    methods=["GET", "POST"],
                    name="removeReadOnly",
                ),
                Route(
                    "/api1/{identity}/updatepricelevel",
                    self.updatepricelevel,
                    methods=["GET", "POST"],
                    name="updatepricelevel",
                ),
                Route(
                    "/api1/{identity}/getquotation",
                    self.getquotation,
                    methods=["GET", "POST"],
                    name="getquotation",
                ),
                Route(
                    "/api1/{identity}/deleteeditquotation",
                    self.deleteeditquotation,
                    methods=["GET", "POST"],
                    name="deleteeditquotation",
                ),
                Route(
                    "/api1/{identity}/print_quotation1",
                    self.print_quotation1,
                    methods=["GET", "POST"],
                    name="print_quotation1",
                ),
                Route(
                    "/api1/{identity}/print_invoice",
                    self.print_invoice,
                    methods=["GET", "POST"],
                    name="print_invoice",
                ),
                Route(
                    "/api1/{identity}/send_email",
                    self.send_email,
                    methods=["POST"],
                    name="send_email",
                ),
                Route(
                    "/api1/{identity}/converttoinvoice",
                    self.converttoinvoice,
                    methods=["GET", "POST"],
                    name="converttoinvoice",
                ),
                Route(
                    "/api1/{identity}/updatestock",
                    self.updatestock,
                    methods=["GET", "POST"],
                    name="updatestock",
                ),
                Route(
                    "/api1/{identity}/items_massupdate",
                    self.items_massupdate,
                    methods=["GET", "POST"],
                    name="items_massupdate",
                ),
                Route(
                    "/api1/{identity}/getitemsmassupdate",
                    self.getitemsmassupdate,
                    methods=["GET", "POST"],
                    name="getitemsmassupdate",
                ),
                Route(
                    "/api1/{identity}/getpolist",
                    self.getpolist,
                    methods=["GET", "POST"],
                    name="getpolist",
                ),
                Route(
                    "/api1/{identity}/printpo",
                    self.printpo,
                    methods=["GET", "POST"],
                    name="printpo",
                ),
                Route(
                    "/api1/{identity}/deletepo",
                    self.deletepo,
                    methods=["GET", "POST"],
                    name="deletepo",
                ),
                Route(
                    "/api1/{identity}/commitpo",
                    self.commitpo,
                    methods=["GET", "POST"],
                    name="commitpo",
                ),
                Route(
                    "/api1/{identity}/productDetails",
                    self.productDetails,
                    methods=["GET", "POST"],
                    name="productDetails",
                ),
                Route(
                    "/api1/{identity}/getpo",
                    self.getpo,
                    methods=["GET", "POST"],
                    name="getpo",
                ),
                Route(
                    "/api1/{identity}/getsupplier",
                    self.getsupplier,
                    methods=["GET", "POST"],
                    name="getsupplier",
                ),
                Route(
                    "/api1/{identity}/shippers",
                    self.shippers,
                    methods=["GET", "POST"],
                    name="shippers",
                ),
                Route(
                    "/api1/{identity}/savepo",
                    self.savepo,
                    methods=["GET", "POST"],
                    name="savepo",
                ),
                Route(
                    "/api1/{identity}/setprogress",
                    self.setprogress,
                    methods=["GET", "POST"],
                    name="setprogress",
                ),
                Route(
                    "/api1/{identity}/updatequtationstatus",
                    self.updatequtationstatus,
                    methods=["GET", "POST"],
                    name="updatequtationstatus",
                ),
            ]
        )
        if self.index_view.add_to_menu:
            self._views.append(self.index_view)

    def _setup_templates(self) -> None:
        templates = Jinja2Templates(self.templates_dir, extensions=["jinja2.ext.i18n"])
        templates.env.loader = ChoiceLoader(
            [
                FileSystemLoader(self.templates_dir),
                PackageLoader("starlette_admin", "templates"),
            ]
        )
        templates.env.globals["views"] = self._views
        templates.env.globals["title"] = self.title
        templates.env.globals["is_auth_enabled"] = self.auth_provider is not None
        templates.env.globals["__name__"] = self.route_name
        templates.env.globals["logo_url"] = self.logo_url
        templates.env.globals["login_logo_url"] = self.login_logo_url
        templates.env.globals["custom_render_js"] = lambda r: self.custom_render_js(r)
        templates.env.globals["get_locale"] = get_locale
        templates.env.globals["get_locale_display_name"] = get_locale_display_name
        templates.env.globals["i18n_config"] = self.i18n_config or I18nConfig()
        templates.env.filters["is_custom_view"] = lambda r: isinstance(r, CustomView)
        templates.env.filters["is_link"] = lambda res: isinstance(res, Link)
        templates.env.filters["is_model"] = lambda res: isinstance(res, BaseModelView)
        templates.env.filters["is_dropdown"] = lambda res: isinstance(res, DropDown)
        templates.env.filters["get_admin_user"] = (
            self.auth_provider.get_admin_user if self.auth_provider else None
        )
        templates.env.filters["tojson"] = lambda data: json.dumps(data, default=str)
        templates.env.filters["file_icon"] = get_file_icon
        templates.env.filters["to_model"] = (
            lambda identity: self._find_model_from_identity(identity)
        )
        templates.env.filters["is_iter"] = lambda v: isinstance(v, (list, tuple))
        templates.env.filters["is_str"] = lambda v: isinstance(v, str)
        templates.env.filters["is_dict"] = lambda v: isinstance(v, dict)
        templates.env.filters["ra"] = lambda a: RequestAction(a)
        templates.env.install_gettext_callables(gettext, ngettext, True)  # type: ignore
        self.templates = templates

    def setup_view(self, view: BaseView) -> None:
        if isinstance(view, DropDown):
            for sub_view in view.views:
                self.setup_view(sub_view)
        elif isinstance(view, CustomView):
            self.routes.insert(
                0,
                Route(
                    view.path,
                    endpoint=self._render_custom_view(view),
                    methods=view.methods,
                    name=view.name,
                ),
            )
        elif isinstance(view, BaseModelView):
            view._find_foreign_model = lambda i: self._find_model_from_identity(i)
            self._models.append(view)

    def _find_model_from_identity(self, identity: Optional[str]) -> BaseModelView:
        if identity is not None:
            for model in self._models:
                if model.identity == identity:
                    return model
        raise HTTPException(
            HTTP_404_NOT_FOUND,
            _("Model with identity %(identity)s not found") % {"identity": identity},
        )

    def _render_custom_view(
        self, custom_view: CustomView
    ) -> Callable[[Request], Awaitable[Response]]:
        async def wrapper(request: Request) -> Response:
            if not custom_view.is_accessible(request):
                raise HTTPException(HTTP_403_FORBIDDEN)
            return await custom_view.render(request, self.templates)

        return wrapper

    async def test_api1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "categories_db1"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all1(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": f"{item[1]}_{item[2]}",
                    "Category": f"{item[0]} --> {item[3]}",
                    "_select2_selection": f"<span><strong>{item[0]} --> {item[3]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[0]} --> {item[3]} </strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def test_api2(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "categories_db2"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all1(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": f"{item[1]}_{item[2]}",
                    "Category": f"{item[0]} --> {item[3]}",
                    "_select2_selection": f"<span><strong>{item[0]} --> {item[3]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[0]} --> {item[3]} </strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def test_api3(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "categories_db3"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        items = await model.find_all1(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": f"{item[1]}_{item[2]}",
                    "Category": f"{item[0]} --> {item[3]}",
                    "_select2_selection": f"<span><strong>{item[0]} --> {item[3]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[0]} --> {item[3]} </strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)

        return JSONResponse(res_dict)
    
    async def test_api4(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "categories_db4"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all1(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": f"{item[1]}_{item[2]}",
                    "Category": f"{item[0]} --> {item[3]}",
                    "_select2_selection": f"<span><strong>{item[0]} --> {item[3]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[0]} --> {item[3]} </strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def manutest1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "manutest1"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        items = await model.find_all_manutest(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)

        return JSONResponse(res_dict)

    async def manutest2(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "manutest2"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        items = await model.find_all_manutest(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def manutest3(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "manutest3"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_manutest(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)
    

    async def manutest4(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "manutest4"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        items = await model.find_all_manutest(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)

        return JSONResponse(res_dict)


    async def unitid1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "unitid1"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_unitid(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def unitid2(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "unitid2"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_unitid(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def unitid3(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "unitid3"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_unitid(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)
    

    async def unitid4(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "unitid4"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_unitid(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)


    async def taxid1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "taxid1"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_tax(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def taxid2(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "taxid2"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_tax(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def taxid3(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "taxid3"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_tax(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)
    

    async def taxid4(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "taxid4"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_tax(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)


    async def prodtempldb1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "prodtempldb1"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_prodtempl(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        if len(items) == 1:
            flag = 0
        else:
            flag = 1
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def prodtempldb2(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "prodtempldb2"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_prodtempl(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        if len(items) == 1:
            flag = 0
        else:
            flag = 1
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def prodtempldb3(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "prodtempldb3"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_prodtempl(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        if len(items) == 1:
            flag = 0
        else:
            flag = 1
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "Manufacturers": f"{item[1]}",
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)
    

    async def prodtempldb4(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "prodtempldb4"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)
        items = await model.find_all_prodtempl(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        if len(items) == 1:
            flag = 0
        else:
            flag = 1
        for item in items:
            res_dict_temp = {}
            res_dict_temp.update(
                {
                    "id": item[0],
                    "_select2_selection": f"<span><strong>{item[1]}</strong></span>",
                    "_select2_result": f"<span><strong>{item[1]}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)


    async def _render_api(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        query_update_quotation: dict[str:str] = dict()
        url_ref: str = ""
        for i in range(len(request.scope["headers"])):
            if len(request.scope["headers"][i]) > 1:
                for i1 in request.scope["headers"][i]:
                    if isinstance(i1, bytes):
                        val_i = i1.decode()
                    else:
                        val_i = i1
                    if val_i == "referer":
                        url_ref = request.scope["headers"][i][1]
        if url_ref:
            query_view_edit_quotation = dict(parse_qsl(urlsplit(str(url_ref)).query))
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        user_account = request.state.user["name"].strip().lower()
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        if len(pks) > 0:
            items = await model.find_by_pks(request, pks)
            total = len(items)
        else:
            if where is not None:
                try:
                    where = json.loads(where)
                except JSONDecodeError:
                    where = str(where)
            if identity == "quotation":
                model = self._find_model_from_identity("quotation")
                total = await model.count(request=request, where=where)
            elif identity == "quotations1_tbl":
                model = self._find_model_from_identity("quotations1_tbl")
                total = 0
            elif identity == "quotations2_tbl":
                model = self._find_model_from_identity("quotations2_tbl")
                form = await request.form()
                query_update_quotation = dict(
                    parse_qsl(urlsplit(str(request.url)).query)
                )
            elif identity == "invoices2_tbl":
                model = self._find_model_from_identity("invoices2_tbl")
                form = await request.form()
                query_update_quotation = dict(
                    parse_qsl(urlsplit(str(request.url)).query)
                )
            elif identity == "quotations3_tbl":
                model = self._find_model_from_identity("quotations3_tbl")
                total = 0
                query_update_quotation_0 = dict(
                    parse_qsl(urlsplit(str(request.url)).query)
                )
                skip = query_update_quotation_0["skip"]
                url_ref: str = ""
                order_by: str = ""
                for i in range(len(request.scope["headers"])):
                    if len(request.scope["headers"][i]) > 1:
                        for i1 in request.scope["headers"][i]:
                            if isinstance(i1, bytes):
                                val_i = i1.decode()
                            else:
                                val_i = i1
                            if val_i == "referer":
                                url_ref = request.scope["headers"][i][1]
                query_update_quotation: dict[str:str] = dict(
                    dict(parse_qsl(urlsplit(str(url_ref)).query)),
                    **query_update_quotation_0,
                )
            elif identity == "quotationsdetails1_tbl":
                model = self._find_model_from_identity("quotationsdetails1_tbl")
                total = 0
            elif identity == "checkinvertory":
                model = self._find_model_from_identity("checkinvertory")
                total = 0
                items = await model.find_all(
                    request=request,
                    skip=skip,
                    limit=limit,
                    where=where,
                    order_by=order_by,
                    query_url=query_update_quotation,
                )
                return JSONResponse(
                    {
                        "items": items,
                        "menu": menu(request),
                    }
                )
            import time
            start_time = time.time()

            items = await model.find_all(
                request=request,
                skip=skip,
                limit=limit,
                where=where,
                order_by=order_by,
                query_url=query_update_quotation,
            )

            find_all_time = time.time() - start_time
            print(f"⏱️ TIMING - find_all(): {find_all_time:.3f}s")

            if identity in ["quotations2_tbl", "invoices2_tbl"]:
                # Use the total count from find_all (stored in request.state)
                total = getattr(request.state, 'quotations_total_count', len(items))
                print(f"⏱️ TOTAL COUNT: {total} (items loaded: {len(items)})")
                items_lists = SPLIT_LIST_TO_LISTS_3(items, limit)
                items_lists_1 = []
                for i1 in items_lists:
                    items_lists_1.append(i1)
            else:
                items_lists_1 = items

        serialize_start = time.time()
        items_serialized = []
        for item in items_lists_1:
            serialized_item = await model.serialize(
                item,
                request,
                RequestAction.API if select2 else RequestAction.LIST,
                include_relationships=not select2,
                include_select2=select2,
                DBD=item["DBname"],
                QuotationID=item.get("QuotationID", "InvoiceID"),
            )
            # Preserve StatusQuotation field from SQL query (not in model.fields)
            if identity == "quotations2_tbl" and "StatusQuotation" in item:
                serialized_item["StatusQuotation"] = item["StatusQuotation"]
            items_serialized.append(serialized_item)

        serialize_time = time.time() - serialize_start
        print(f"⏱️ TIMING - serialization: {serialize_time:.3f}s ({len(items_serialized)} items)")

        if identity == "quotations2_tbl":
            # StatusQuotation is now included in SQL query, no enrichment needed
            # Profit margin enrichment still happens if needed
            enrich_start = time.time()
            model.bulk_load_additional_quotation_data(items_serialized)
            enrich_time = time.time() - enrich_start
            print(f"⏱️ TIMING - enrichment: {enrich_time:.3f}s")

        # Include unique sales reps in response if available (for dropdown population)
        response_data = {"items": items_serialized, "total": total}
        if hasattr(request.state, 'unique_sales_reps'):
            response_data["unique_sales_reps"] = request.state.unique_sales_reps

        # Debug: Print sample item to verify StatusQuotation values
        if identity == "quotations2_tbl" and items_serialized:
            print(f"🔍 SAMPLE ITEM: {items_serialized[0]}")
            print(f"🔍 StatusQuotation values: {[item.get('StatusQuotation') for item in items_serialized[:3]]}")

        return JSONResponse(response_data)

    async def handle_action(self, request: Request) -> Response:
        try:
            identity = request.path_params.get("identity")
            pks = request.query_params.getlist("pks")
            name = request.query_params.get("name")
            model = self._find_model_from_identity(identity)
            if not model.is_accessible(request):
                raise ActionFailed("Forbidden")
            assert name is not None
            handler_return = await model.handle_action(request, pks, name)
            if isinstance(handler_return, Response):
                return handler_return
            return JSONResponse({"msg": handler_return})
        except ActionFailed as exc:
            return JSONResponse({"msg": exc.msg}, status_code=HTTP_400_BAD_REQUEST)

    async def _render_login(self, request: Request) -> Response:
        if request.method == "GET":
            return self.templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "_is_login_path": True,
                    "menu": menu(request),
                },
            )
        form = await request.form()
        try:
            assert self.auth_provider is not None
            return await self.auth_provider.login(
                form.get("username"),  # type: ignore
                form.get("password"),  # type: ignore
                form.get("remember_me") == "on",
                request,
                RedirectResponse(
                    request.query_params.get("next")
                    or request.url_for(self.route_name + ":index"),
                    status_code=HTTP_303_SEE_OTHER,
                ),
            )
        except FormValidationError as errors:
            return self.templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "form_errors": errors,
                    "_is_login_path": True,
                    "menu": menu(request),
                },
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except LoginFailed as error:
            return self.templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": error.msg,
                    "_is_login_path": True,
                    "menu": menu(request),
                },
                status_code=HTTP_400_BAD_REQUEST,
            )

    async def _render_logout(self, request: Request) -> Response:
        assert self.auth_provider is not None
        return await self.auth_provider.logout(
            request,
            RedirectResponse(
                request.url_for(self.route_name + ":index"),
                status_code=HTTP_303_SEE_OTHER,
            ),
        )

    async def _render_list(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        return self.templates.TemplateResponse(
            model.list_template,
            {
                "request": request,
                "model": model,
                "_actions": await model.get_all_actions(request),
                "__js_model__": await model._configs(request),
                "menu": menu(request),
            },
        )

    async def _render_detail(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_view_details(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        pk = request.path_params.get("pk")
        obj = await model.find_by_pk(request, pk)
        if obj is None:
            raise HTTPException(HTTP_404_NOT_FOUND)
        obj_detail = await model.serialize(obj, request, RequestAction.DETAIL)
        return self.templates.TemplateResponse(
            model.detail_template,
            {
                "request": request,
                "model": model,
                "raw_obj": obj,
                "obj": obj_detail,
                "menu": menu(request),
            },
        )

    async def _render_create(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        if not model.is_accessible(request) or not model.can_create(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        if request.method == "GET":
            return self.templates.TemplateResponse(
                model.create_template,
                {
                    "request": request,
                    "model": model,
                    "menu": menu(request),
                },
            )
        try:
            obj = await model.create(request, dict_obj)
        except FormValidationError as exc:
            return self.templates.TemplateResponse(
                model.create_template,
                {
                    "request": request,
                    "model": model,
                    "errors": exc.errors,
                    "obj": dict_obj,
                    "menu": menu(request),
                },
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )
        pk = getattr(obj, model.pk_attr)  # type: ignore
        url = request.url_for(self.route_name + ":list", identity=model.identity)
        if form.get("_continue_editing", None) is not None:
            url = request.url_for(
                self.route_name + ":edit", identity=model.identity, pk=pk
            )
        elif form.get("_add_another", None) is not None:
            url = request.url
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    async def _render_create1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        form = await request.form()
        user_account = request.state.user["name"].strip().lower()
        statususer = request.state.user["statususer"]
        if not model.is_accessible(request) or not model.can_create(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        identity_req = request.path_params["identity"]
        if identity_req == "items_tbl":
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            if (
                request.method == "GET"
                and dict_obj["Prodtempl1"] == None
                and dict_obj["ProductUPC"] == None
            ):
                return self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
        elif identity_req == "invoices_tbl":
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            form = await request.form()
            if "_choicedbdestination1" in form:
                pass
            if request.method == "GET":
                return self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )

        elif identity_req == "quotations_tbl":
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            if request.method == "GET":
                model11 = self._find_model_from_identity("quotation")
                get_all_actions = await model11.get_all_actions(request)
                config_model = await model11._configs(request)
                return self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
        elif identity_req == "quotations1_tbl":
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            if request.method == "GET":
                model11 = self._find_model_from_identity("quotations1_tbl")
                get_all_actions = await model11.get_all_actions(request)
                config_model = await model11._configs(request)
                with Session(engine["DB_admin"]) as session1:
                    stmt_quotation_status = select(
                        QuotationsTemp.__table__.columns
                    ).filter_by(SessionID=user_account)
                    rows_quotation_status = (
                        session1.execute(stmt_quotation_status).mappings().all()
                    )
                if rows_quotation_status:
                    dict_obj.update({"SourceDB": rows_quotation_status[0]["SourceDB"]})
                    dict_obj.update(
                        {"BusinessName": rows_quotation_status[0]["BusinessName"]}
                    )
                    dict_obj.update(
                        {"AccountNo": rows_quotation_status[0]["AccountNo"]}
                    )
                return self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
        elif identity_req == "invoices2_tbl":
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            if request.method == "GET" or request.method == "POST":
                model11 = self._find_model_from_identity("invoices2_tbl")
                form = await request.form()
                lab = "Invoices List"
                dict_obj = await self.form_to_dict(
                    request, form, model11, RequestAction.CREATE
                )
                get_all_actions = await model11.get_all_actions(request)
                config_model = await model11._configs(
                    request, dop=dict_obj["choicedb_source"]
                )
                with Session(engine["DB_admin"]) as session:
                    query_invoices2_tbl_accessdb = select(
                        AdminUserProject_admin.__table__.columns
                    ).filter_by(username=user_account)
                    answ_invoices2_tbl_accessdb = (
                        session.execute(query_invoices2_tbl_accessdb).mappings().all()
                    )
                dict_obj_db_list: dict[str:str] = dict()
                for i in answ_invoices2_tbl_accessdb[0]["accessdb"].split("/"):
                    dict_obj_db_list[engine_nick[i]] = i
                dict_obj.update({"db_list": dict_obj_db_list})
                dict_obj.update({"label": f"{lab.upper()}"})
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        
        elif identity_req == "InvoicesDetails_tbl":
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            if request.method == "GET":
                model11 = self._find_model_from_identity("InvoicesDetails_tbl")
                get_all_actions = await model11.get_all_actions(request)
                config_model = await model11._configs(request)
                with Session(engine["DB_admin"]) as session1:
                    stmt_quotation_status = select(
                        QuotationsTemp.__table__.columns
                    ).filter_by(SessionID=user_account)
                    rows_quotation_status = (
                        session1.execute(stmt_quotation_status).mappings().all()
                    )
                if rows_quotation_status:
                    dict_obj.update({"SourceDB": rows_quotation_status[0]["SourceDB"]})
                    dict_obj.update(
                        {"BusinessName": rows_quotation_status[0]["BusinessName"]}
                    )
                    dict_obj.update(
                        {"AccountNo": rows_quotation_status[0]["AccountNo"]}
                    )
                return self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )

        elif identity_req == "quotations2_tbl":
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            if request.method == "GET" or request.method == "POST":
                model11 = self._find_model_from_identity("quotations2_tbl")
                form = await request.form()
                lab = "Quotations List"
                dict_obj = await self.form_to_dict(
                    request, form, model11, RequestAction.CREATE
                )
                get_all_actions = await model11.get_all_actions(request)
                config_model = await model11._configs(
                    request, dop=dict_obj["choicedb_source"]
                )
                with Session(engine["DB_admin"]) as session:
                    query_quotations2_tbl_accessdb = select(
                        AdminUserProject_admin.__table__.columns
                    ).filter_by(username=user_account)
                    answ_quotations2_tbl_accessdb = (
                        session.execute(query_quotations2_tbl_accessdb).mappings().all()
                    )
                dict_obj_db_list: dict[str:str] = dict()
                for i in answ_quotations2_tbl_accessdb[0]["accessdb"].split("/"):
                    dict_obj_db_list[engine_nick[i]] = i
                dict_obj.update({"db_list": dict_obj_db_list})
                dict_obj.update({"label": f"{lab.upper()}"})
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

        elif identity_req == "quotations3_tbl":
            form = await request.form()
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            dict_obj.pop("Total")
            model11 = self._find_model_from_identity("quotations3_tbl")
            get_all_actions = await model11.get_all_actions(request)
            config_model = await model11._configs(request)
            query_update_quotation = dict(parse_qsl(urlsplit(str(request.url)).query))
            QuotationNumber = query_update_quotation["QuotationNumber"]
            ProductSKU = dict_obj["ProductSKU"]
            if request.method == "GET":
                with Session(
                    engine[engine_nick[query_update_quotation["DBname"]]]
                ) as session1:
                    stmt_quotation_status = select(
                        Quotations_tbl.__table__.columns
                    ).filter_by(QuotationNumber=QuotationNumber)
                    rows_quotation_status = (
                        session1.execute(stmt_quotation_status).mappings().all()
                    )
                if rows_quotation_status:
                    dict_obj.update({"SourceDB": query_update_quotation["DBname"]})
                    dict_obj.update(
                        {"BusinessName": rows_quotation_status[0]["BusinessName"]}
                    )
                    dict_obj.update(
                        {"AccountNo": rows_quotation_status[0]["AccountNo"]}
                    )
                    dict_obj.update({"QuotationNumber": QuotationNumber})
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            if form.get("_checkdb_quotation_edit", None) is not None:
                ProductSKU: str = str()
                ProductDescription: str = str()
                errors: str = str()
                successfully: str = str()
                for i in dict_obj:
                    if dict_obj[i] == None:
                        errors = "Fill in all the required fields"
                        break
                    if i == "Qty":
                        if not dict_obj[i].isdigit() or not dict_obj[i]:
                            errors = "Qty parameter must be a number and have a value greater than zero"
                            break
                        else:
                            if int(dict_obj[i]) <= 0:
                                errors = "Qty parameter must be a number and have a value greater than zero"
                                break
                    elif i == "UnitPrice":
                        if checking_str(dict_obj[i]) == "str" or not dict_obj[i]:
                            errors = "UnitPrice parameter must be an integer or a decimal number"
                            break
                QuotationID = query_update_quotation["QuotationID"]
                QuotationNumber = query_update_quotation["QuotationNumber"]
                ProductDescription = dict_obj["ProductDescription"]
                ProductSKU = dict_obj["ProductSKU"]
                Qty = dict_obj["Qty"]
                UnitPrice = dict_obj["UnitPrice"]
                ExpirationDate = (
                    datetime.datetime.today() + datetime.timedelta(days=10)
                ).strftime("%Y-%m-%d 00:00:00")
                with Session(
                    engine[engine_nick[query_update_quotation["DBname"]]]
                ) as session:
                    stmt_check_items = select(
                        QuotationsDetails_tbl.__table__.columns
                    ).where(
                        and_(
                            QuotationsDetails_tbl.ProductSKU == ProductSKU,
                            QuotationsDetails_tbl.QuotationID == QuotationID,
                        )
                    )
                    rows_check_items = (
                        session.execute(stmt_check_items).mappings().all()
                    )
                    if rows_check_items:
                        errors = f"This Item {ProductSKU} already present in Quotation {QuotationNumber}"
                if not errors:
                    with Session(
                        engine[engine_nick[query_update_quotation["DBname"]]]
                    ) as session:
                        stmt_quotation_items = select(
                            Items_tbl.__table__.columns
                        ).filter_by(ProductSKU=ProductSKU)
                        rows_quotation_items = (
                            session.execute(stmt_quotation_items).mappings().all()
                        )
                        stmt_quotation_UnitDesc = select(
                            Units_tbl.__table__.columns
                        ).filter_by(UnitID=str(rows_quotation_items[0]["UnitID"]))
                        rows_quotation_UnitDesc = (
                            session.execute(stmt_quotation_UnitDesc).mappings().all()
                        )
                        if rows_quotation_UnitDesc:
                            UnitDesc = rows_quotation_UnitDesc[0]["UnitDesc"]
                        else:
                            UnitDesc = ""
                        stmt_quotationsdetails = (
                            insert(QuotationsDetails_tbl)
                            .values(
                                QuotationID=QuotationID,
                                CateID=rows_quotation_items[0]["CateID"],
                                SubCateID=rows_quotation_items[0]["SubCateID"],
                                ProductID=rows_quotation_items[0]["ProductID"],
                                ProductSKU=ProductSKU,
                                ProductUPC=rows_quotation_items[0]["ProductUPC"],
                                ProductDescription=ProductDescription,
                                ItemSize=rows_quotation_items[0]["ItemSize"],
                                ExpDate=ExpirationDate,
                                UnitPrice=round(float(UnitPrice), 2),
                                OriginalPrice=round(float(UnitPrice), 2),
                                UnitCost=rows_quotation_items[0]["UnitCost"],
                                Qty=int(Qty),
                                ItemWeight=rows_quotation_items[0]["ItemWeight"],
                                Discount=0,
                                ds_Percent=0,
                                ExtendedPrice=round(float(UnitPrice), 2) * int(Qty),
                                ExtendedCost=rows_quotation_items[0]["UnitCost"]
                                * int(Qty),
                                ExtendedDisc=0,
                                PromotionID=0,
                                PromotionLine=0,
                                SPPromoted=0,
                                Taxable=0,
                                ItemTaxID=0,
                                Catch=0,
                                Flag=0,
                                ActExtendedPrice=round(float(UnitPrice), 2) * int(Qty),
                                UnitDesc=UnitDesc,
                            )
                            .returning(
                                QuotationsDetails_tbl.LineID,
                            )
                        )

                        rows_quotationsdetails = (
                            session.execute(stmt_quotationsdetails).mappings().all()
                        )
                        session.commit()
                        stmt_quotation_delete_sum = select(
                            QuotationsDetails_tbl.UnitPrice,
                            QuotationsDetails_tbl.Qty,
                        ).where(
                            QuotationsDetails_tbl.QuotationID == QuotationID,
                        )
                        rows_quotation_delete_sum = (
                            session.execute(stmt_quotation_delete_sum).mappings().all()
                        )
                        total_sum: list[str] = list()
                        for i in rows_quotation_delete_sum:
                            total_sum.append(float(i["UnitPrice"]) * float(i["Qty"]))
                        stmt_delete_quotation_sum = (
                            update(Quotations_tbl)
                            .values(
                                QuotationTotal=sum(total_sum),
                            )
                            .where(Quotations_tbl.QuotationID == QuotationID)
                        )
                        answ_update_quotation_details = session.execute(
                            stmt_delete_quotation_sum
                        )
                        session.commit()
                        successfully = f"Item {ProductDescription} successfully added in Quotation {QuotationNumber}"
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "update_error": errors,
                        "update": successfully,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            elif form.get("_productskudescription_quotation_edit", None) is not None:
                ProductSKU: str = str()
                with Session(
                    engine[engine_nick[query_update_quotation["DBname"]]]
                ) as session:
                    stmt_quotation_status = select(
                        Items_tbl.__table__.columns
                    ).filter_by(ProductDescription=dict_obj["ProductDescription"])
                    rows_quotation_status = (
                        session.execute(stmt_quotation_status).mappings().all()
                    )
                    if rows_quotation_status:
                        ProductSKU = rows_quotation_status[0]["ProductSKU"]
                        UnitPrice = rows_quotation_status[0]["UnitPrice"]
                        dict_obj.update({"ProductSKU": ProductSKU})
                        dict_obj.update({"UnitPrice": round(UnitPrice, 2)})
                    query_item_price = (
                        select(
                            InvoicesDetails_tbl.__table__.columns,
                            Invoices_tbl.AccountNo,
                        )
                        .join(
                            Invoices_tbl,
                            Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID,
                        )
                        .where(
                            and_(
                                Invoices_tbl.AccountNo == dict_obj["AccountNo"],
                                InvoicesDetails_tbl.ProductSKU
                                == rows_quotation_status[0]["ProductSKU"],
                            )
                        )
                        .order_by(InvoicesDetails_tbl.UnitPrice.desc())
                    )

                    answ_item_price = session.execute(query_item_price).mappings().all()
                    if answ_item_price:
                        dict_obj.update(
                            {"UnitPrice": round(answ_item_price[0]["UnitPrice"], 2)}
                        )
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            elif form.get("_productsku_quotation_edit", None) is not None:
                ProductSKU: str = str()
                ProductDescription: str = str()

                with Session(
                    engine[engine_nick[query_update_quotation["DBname"]]]
                ) as session:
                    stmt_quotation_status = select(
                        Items_tbl.__table__.columns
                    ).filter_by(ProductSKU=dict_obj["ProductSKU"])
                    rows_quotation_status = (
                        session.execute(stmt_quotation_status).mappings().all()
                    )
                    if rows_quotation_status:
                        ProductDescription = rows_quotation_status[0][
                            "ProductDescription"
                        ]
                        UnitPrice = rows_quotation_status[0]["UnitPrice"]
                        dict_obj.update({"ProductDescription": ProductDescription})
                        dict_obj.update({"UnitPrice": round(UnitPrice, 2)})
                    query_item_price = (
                        select(
                            InvoicesDetails_tbl.__table__.columns,
                            Invoices_tbl.AccountNo,
                        )
                        .join(
                            Invoices_tbl,
                            Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID,
                        )
                        .where(
                            and_(
                                Invoices_tbl.AccountNo == dict_obj["AccountNo"],
                                InvoicesDetails_tbl.ProductSKU
                                == rows_quotation_status[0]["ProductSKU"],
                            )
                        )
                        .order_by(InvoicesDetails_tbl.UnitPrice.desc())
                    )
                    answ_item_price = session.execute(query_item_price).mappings().all()
                    if answ_item_price:
                        dict_obj.update(
                            {"UnitPrice": round(answ_item_price[0]["UnitPrice"], 2)}
                        )
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            elif form.get("_checkaccountnoquotation_quotation_edit", None) is not None:
                ProductSKU: str = str()
                ProductDescription: str = str()
                with Session(
                    engine[engine_nick[query_update_quotation["DBname"]]]
                ) as session:
                    stmt_quotation_status = select(
                        Customers_tbl.__table__.columns
                    ).filter_by(AccountNo=dict_obj["AccountNo"])
                    rows_quotation_status = (
                        session.execute(stmt_quotation_status).mappings().all()
                    )
                    if rows_quotation_status:
                        AccountNo = rows_quotation_status[0]["AccountNo"]
                        BusinessName = rows_quotation_status[0]["BusinessName"]
                        dict_obj.update({"AccountNo": AccountNo})
                        dict_obj.update({"BusinessName": BusinessName})
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            elif (
                form.get("_checkbusinessnamequotation_quotation_edit", None) is not None
            ):
                ProductSKU: str = str()
                ProductDescription: str = str()
                with Session(
                    engine[engine_nick[query_update_quotation["DBname"]]]
                ) as session:
                    stmt_quotation_status = select(
                        Customers_tbl.__table__.columns
                    ).filter_by(BusinessName=dict_obj["BusinessName"])
                    rows_quotation_status = (
                        session.execute(stmt_quotation_status).mappings().all()
                    )
                    if rows_quotation_status:
                        AccountNo = rows_quotation_status[0]["AccountNo"]
                        BusinessName = rows_quotation_status[0]["BusinessName"]
                        dict_obj.update({"AccountNo": AccountNo})
                        dict_obj.update({"BusinessName": BusinessName})
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        elif identity_req == "quotationsdetails1_tbl":
            list_obj_detail: list[str] = list()
            if request.method == "GET":
                model11 = self._find_model_from_identity("quotationsdetails1_tbl")
                get_all_actions = await model11.get_all_actions(request)
                config_model = await model11._configs(request)
                query_update_quotation = dict(
                    parse_qsl(urlsplit(str(request.url)).query)
                )
                dict_obj: dict[str:str] = dict()
                with Session(
                    engine[engine_nick[query_update_quotation["DBname"]]]
                ) as session:
                    stmt_quotation_edit = select(
                        Quotations_tbl.__table__.columns
                    ).filter_by(
                        QuotationNumber=query_update_quotation["QuotationNumber"]
                    )
                    rows_quotation_edit = (
                        session.execute(stmt_quotation_edit).mappings().all()
                    )
                    dict_obj.update({"SourceDB": query_update_quotation["DBname"]})
                    dict_obj.update(
                        {"QuotationNumber": query_update_quotation["QuotationNumber"]}
                    )
                    dict_obj.update(
                        {"BusinessName": rows_quotation_edit[0]["BusinessName"]}
                    )
                    dict_obj.update({"AccountNo": rows_quotation_edit[0]["AccountNo"]})
                    dict_obj.update(
                        {"QuotationID": rows_quotation_edit[0]["QuotationID"]}
                    )
                    dict_obj.update(
                        {
                            "Total": f"${round(rows_quotation_edit[0]['QuotationTotal'], 2)}"
                        }
                    )
                    stmt_quotation_edit_det = select(
                        QuotationsDetails_tbl.LineID
                    ).filter_by(QuotationID=query_update_quotation["QuotationID"])
                    rows_quotation_edit_det = (
                        session.execute(stmt_quotation_edit_det).mappings().all()
                    )
                    dict_obj.update({"Total Items": f"{len(rows_quotation_edit_det)}"})
                response = self.templates.TemplateResponse(
                    "edit_quotation.html",
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        elif identity_req == "checkinvertory":
            list_obj_detail: list[str] = list()
            model = self._find_model_from_identity("checkinvertory")
            get_all_actions = await model.get_all_actions(request)
            config_model = await model._configs(request)
            response = self.templates.TemplateResponse(
                "checkinvertory.html",
                {
                    "request": request,
                    "model": model,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif identity_req == "manualinventoryupdate":
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%m-%d-%Y %H:%M:%S")
            errors_update_inventory = ""
            update_inventory = ""
            update_inventory_inprogress = []
            po_inventory_inprogress = []
            bin_locations_display = ""
            statususer = request.state.user["statususer"].strip().lower()
            form = await request.form()

            # Helper function to parse time from Dop2/Dop3 fields
            def parse_time_from_dop(dop_value):
                """Extract time in 12-hour format with AM/PM from Dop timestamp string"""
                if not dop_value:
                    return "--"

                # Try common datetime formats found in the codebase
                formats = [
                    "%m/%d/%Y %I:%M %p",      # 10/27/2025 2:30 PM
                    "%m-%d-%Y %H:%M:%S",      # 10-27-2025 14:30:45
                    "%Y-%m-%d %H:%M:%S",      # 2025-10-27 14:30:45
                    "%m/%d/%Y %H:%M:%S",      # 10/27/2025 14:30:45
                    "%m/%d/%Y %H:%M",         # 10/27/2025 14:30
                    "%m-%d-%Y %I:%M %p",      # 10-27-2025 2:30 PM
                ]

                for fmt in formats:
                    try:
                        dt = datetime.datetime.strptime(dop_value.strip(), fmt)
                        return dt.strftime("%-I:%M %p")  # Format: 2:30 PM (no leading zero)
                    except:
                        continue

                return "--"  # If all parsing fails

            # Helper function to fetch and format bin locations
            def get_bin_locations_display(product_upc, session):
                """
                Fetch all bin locations for a product and format as display string.
                Returns: "A-12 (50 items), B-05 (30 items) | Total: 80 items" or "No bins"
                """
                # Use raw SQL with text() for the UnitQty2 column that's not in the model
                stmt_bins = text("""
                    SELECT
                        bl.BinLocation,
                        ibl.Qty_Cases,
                        ISNULL(it.UnitQty2, 0) as UnitQty2
                    FROM Items_BinLocations ibl
                    JOIN BinLocations_tbl bl ON ibl.BinLocationID = bl.BinLocationID
                    LEFT JOIN Items_tbl it ON ibl.ProductUPC = it.ProductUPC
                    WHERE ibl.ProductUPC = :product_upc
                """)

                bin_results = session.execute(stmt_bins, {"product_upc": product_upc}).all()

                if not bin_results:
                    return "No bins"

                # Build list of "BinName (qty items)" strings and calculate grand total
                bin_displays = []
                grand_total = 0
                for row in bin_results:
                    bin_name = row[0] if row[0] else "Unnamed"
                    qty_cases = row[1] if row[1] else 0
                    unit_qty2 = row[2] if row[2] else 0
                    total_items = qty_cases * unit_qty2
                    grand_total += total_items
                    bin_displays.append(f"{bin_name} ({total_items} items)")

                # Sort alphabetically and join with comma
                bin_displays.sort()
                bins_part = ", ".join(bin_displays)

                # Add total with HTML span for color styling (blue color)
                return f'{bins_part} | <span style="color: #1a73e8; font-weight: bold;">Total: {grand_total} items</span>'

            ProductDescription = dict_obj["ProductDescription"]
            SKU = dict_obj["SKU"]
            ProductUPC = dict_obj["ProductUPC"]
            with Session(engine["DB1"]) as session:
                stmt_Items_tbl = select(
                    Items_tbl.__table__.columns,
                )
                if ProductUPC and ProductDescription == None and SKU == None:
                    stmt_Items_tbl = stmt_Items_tbl.where(
                        and_(
                            Items_tbl.ProductUPC == ProductUPC,
                            Items_tbl.Discontinued == 0,
                        )
                    )
                    answ_Items_tbl = session.execute(stmt_Items_tbl).mappings().all()
                    if len(answ_Items_tbl) > 1:
                        errors_update_inventory = (
                            f"UPC: {ProductUPC} has duplicates in database"
                        )
                        response = self.templates.TemplateResponse(
                            "manualupdate.html",
                            {
                                "request": request,
                                "model": model,
                                "obj": dict_obj,
                                "update": update_inventory,
                                "update_error": errors_update_inventory,
                                "bin_locations": bin_locations_display,
                                "po_inprogress": po_inventory_inprogress,
                                "menu": menu(request),
                            },
                        )
                        response.headers["Cache-Control"] = (
                            "no-store, no-cache, must-revalidate, max-age=0"
                        )
                        response.headers["Pragma"] = "no-cache"
                        response.headers["Expires"] = "0"
                        return response

                    if not answ_Items_tbl:
                        errors_update_inventory = f"UPC: {ProductUPC} not found"
                        response = self.templates.TemplateResponse(
                            "manualupdate.html",
                            {
                                "request": request,
                                "model": model,
                                "obj": dict_obj,
                                "update": update_inventory,
                                "update_error": errors_update_inventory,
                                "bin_locations": bin_locations_display,
                                "po_inprogress": po_inventory_inprogress,
                                "menu": menu(request),
                            },
                        )
                        response.headers["Cache-Control"] = (
                            "no-store, no-cache, must-revalidate, max-age=0"
                        )
                        response.headers["Pragma"] = "no-cache"
                        response.headers["Expires"] = "0"
                        return response
                    else:
                        dict_obj.update({"SKU": answ_Items_tbl[0]["ProductSKU"]})
                        dict_obj.update({"Qty": answ_Items_tbl[0]["QuantOnHand"]})
                        dict_obj.update({"ProductID": answ_Items_tbl[0]["ProductID"]})
                        dict_obj.update({"ProductUPC": answ_Items_tbl[0]["ProductUPC"]})
                        dict_obj.update(
                            {
                                "ProductDescription": answ_Items_tbl[0][
                                    "ProductDescription"
                                ]
                            }
                        )
                if "_productskumanual" in form:
                    stmt_Items_tbl = stmt_Items_tbl.where(
                        and_(
                            Items_tbl.ProductSKU == SKU,
                            Items_tbl.Discontinued == 0,
                        )
                    )
                    answ_Items_tbl = session.execute(stmt_Items_tbl).mappings().all()
                    dict_obj.update(
                        {"ProductDescription": answ_Items_tbl[0]["ProductDescription"]}
                    )
                    dict_obj.update({"SKU": answ_Items_tbl[0]["ProductSKU"]})
                    dict_obj.update({"Qty": answ_Items_tbl[0]["QuantOnHand"]})
                    dict_obj.update({"ProductID": answ_Items_tbl[0]["ProductID"]})
                    dict_obj.update({"ProductUPC": answ_Items_tbl[0]["ProductUPC"]})
                elif "_productdescriptionmanual" in form:
                    stmt_Items_tbl = stmt_Items_tbl.where(
                        and_(
                            Items_tbl.ProductDescription == ProductDescription,
                            Items_tbl.Discontinued == 0,
                        )
                    )
                    answ_Items_tbl = session.execute(stmt_Items_tbl).mappings().all()
                    dict_obj.update(
                        {"ProductDescription": answ_Items_tbl[0]["ProductDescription"]}
                    )
                    dict_obj.update({"SKU": answ_Items_tbl[0]["ProductSKU"]})
                    dict_obj.update({"Qty": answ_Items_tbl[0]["QuantOnHand"]})
                    dict_obj.update({"ProductID": answ_Items_tbl[0]["ProductID"]})
                    dict_obj.update({"ProductUPC": answ_Items_tbl[0]["ProductUPC"]})
            if dict_obj["ProductUPC"] and dict_obj["ProductUPC"] != None:
                ProductUPC = dict_obj["ProductUPC"]

                # Fetch bin locations for this product
                with Session(engine["DB1"]) as bin_session:
                    bin_locations_display = get_bin_locations_display(ProductUPC, bin_session)

                list_dbs = ["DB1", "DB2", "DB3", "DB14"]
                time_20d = datetime.datetime.today() - datetime.timedelta(days=200)
                qty_list = list()

                with Session(engine["DB_admin"]) as admin_sess:
                    exclude_set = set(
                        admin_sess.execute(
                            select(QuotationsStatus.QuotationNumber)
                            .where(
                                or_(
                                    QuotationsStatus.Status.in_(["New", "CONVERTED", "Converted"]),
                                    and_(
                                        QuotationsStatus.Dop2.is_(None),
                                        QuotationsStatus.Dop3.is_(None),
                                    ),
                                )
                            )
                        ).scalars()
                    )
                    all_set = set(
                        admin_sess.execute(
                            select(QuotationsStatus.QuotationNumber)
                        ).scalars()
                    )

                for dbname in list_dbs:
                    with Session(engine[dbname]) as session:
                        stmt = (
                            select(
                                Quotations_tbl.QuotationID,
                                Quotations_tbl.QuotationDate,
                                Quotations_tbl.QuotationNumber,
                                Quotations_tbl.AccountNo,
                                QuotationsDetails_tbl.__table__.columns,
                            )
                            .join(
                                QuotationsDetails_tbl,
                                Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                            )
                            .where(
                                and_(
                                    QuotationsDetails_tbl.ProductUPC == ProductUPC,
                                    Quotations_tbl.QuotationDate > time_20d,
                                    Quotations_tbl.AutoOrderNo == None,
                                )
                            )
                        )
                        all_rows = session.execute(stmt).mappings().all()

                        # Exclude Quotation Status "New" and "Converted" or without status.
                        answ_check_inprogress = [
                            row for row in all_rows
                            if row["QuotationNumber"] in all_set
                            and row["QuotationNumber"] not in exclude_set
                        ]

                        if answ_check_inprogress:
                            for i in answ_check_inprogress:
                                i = dict(i)
                                if i["AccountNo"] == "missproducts":
                                    continue
                                QuotationNumber = i["QuotationNumber"]
                                QuotationID = i["QuotationID"]
                                stmt_check_inprogress_Employees_tbl = (
                                    select(
                                        Quotations_tbl.AccountNo,
                                        Employees_tbl.FirstName.label("SalesFirstName"),
                                    )
                                    .join(
                                        Employees_tbl,
                                        Quotations_tbl.SalesRepID
                                        == Employees_tbl.EmployeeID,
                                    )
                                    .where(
                                        Quotations_tbl.QuotationID == QuotationID,
                                    )
                                )
                                answ_check_inprogress_Employees_tbl = (
                                    session.execute(stmt_check_inprogress_Employees_tbl)
                                    .mappings()
                                    .all()
                                )
                                if answ_check_inprogress_Employees_tbl:
                                    SalesFirstName = (
                                        answ_check_inprogress_Employees_tbl[0][
                                            "SalesFirstName"
                                        ]
                                    )
                                else:
                                    SalesFirstName = "No data"

                                # Fetch Packer, Dop2, Dop3 from QuotationsStatus table
                                with Session(engine["DB_admin"]) as admin_sess:
                                    stmt_get_packer = select(
                                        QuotationsStatus.Packer,
                                        QuotationsStatus.Dop2,
                                        QuotationsStatus.Dop3
                                    ).where(
                                        QuotationsStatus.QuotationNumber == QuotationNumber
                                    )
                                    packer_row = admin_sess.execute(stmt_get_packer).first()

                                    if packer_row:
                                        packer_name = packer_row[0] if packer_row[0] else "No data"
                                        dop2_time = parse_time_from_dop(packer_row[1])
                                        dop3_time = parse_time_from_dop(packer_row[2])
                                    else:
                                        packer_name = "No data"
                                        dop2_time = "--"
                                        dop3_time = "--"

                                qty_list.append(int(i["Qty"]))
                                temp_update_inventory_inprogress = {
                                    "Number": QuotationNumber,
                                    "Type": "Quotation",
                                    "QuotationDate": i["QuotationDate"].strftime(
                                        "%m-%d-%Y"
                                    ),
                                    "SalesFirstName": SalesFirstName,
                                    "AccountNo": i["AccountNo"],
                                    "BinLocations": bin_locations_display,
                                    "Packer": packer_name,
                                    "Dop2Time": dop2_time,
                                    "Dop3Time": dop3_time,
                                    "QTY": i["Qty"],
                                }
                                update_inventory_inprogress.append(
                                    temp_update_inventory_inprogress
                                )
                with Session(engine[engine_nick["Shipper Platform"]]) as session3:
                    time_now_5h = (
                        datetime.datetime.today() - datetime.timedelta(hours=5)
                    ).date()
                    time_now_5h_min = (
                        datetime.datetime.today() - datetime.timedelta(hours=5)
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    stmt_check_ship = (
                        select(
                            pick_lists.cdate,
                            pick_list_products.__table__.columns,
                        )
                        .join(
                            pick_lists,
                            pick_list_products.id_pick_list == pick_lists.id,
                        )
                        .where(
                            and_(
                                pick_lists.is_printed == 1,
                                cast(pick_lists.cdate, Date) == time_now_5h,
                                pick_list_products.barcode == ProductUPC,
                            )
                        )
                    )
                    answ_check_ship = session3.execute(stmt_check_ship).mappings().all()
                if answ_check_ship:
                    for i in answ_check_ship:
                        i = dict(i)
                        temp_update_inventory_inprogress = {
                            "Number": i["id_pick_list"],
                            "Type": "Internet",
                            "QuotationDate": i["cdate"].strftime("%m-%d-%Y"),
                            "SalesFirstName": "No Data",
                            "AccountNo": "No Data",
                            "BinLocations": bin_locations_display,
                            "Packer": "No Data",
                            "Dop2Time": "--",
                            "Dop3Time": "--",
                            "QTY": i["amount"],
                        }
                        update_inventory_inprogress.append(
                            temp_update_inventory_inprogress
                        )

                # Purchase Orders - query only from DB1
                with Session(engine["DB1"]) as session_po:
                    stmt_check_po = (
                        select(
                            PurchaseOrders_tbl.PoID,
                            PurchaseOrders_tbl.PoDate,
                            PurchaseOrders_tbl.PoNumber,
                            PurchaseOrders_tbl.AccountNo,
                            PurchaseOrdersDetails_tbl.__table__.columns,
                        )
                        .join(
                            PurchaseOrdersDetails_tbl,
                            PurchaseOrders_tbl.PoID
                            == PurchaseOrdersDetails_tbl.PoID,
                        )
                        .where(
                            and_(
                                PurchaseOrdersDetails_tbl.ProductUPC == ProductUPC,
                                PurchaseOrders_tbl.PoDate > time_20d,
                                PurchaseOrders_tbl.Status == 0,
                            )
                        )
                    )
                    answ_check_po = session_po.execute(stmt_check_po).mappings().all()

                    if answ_check_po:
                        for i in answ_check_po:
                            i = dict(i)
                            if i["AccountNo"] == "missproducts":
                                continue
                            PoNumber = i["PoNumber"]
                            PoID = i["PoID"]
                            stmt_check_po_Employees_tbl = (
                                select(
                                    PurchaseOrders_tbl.AccountNo,
                                    Employees_tbl.FirstName.label("SalesFirstName"),
                                )
                                .join(
                                    Employees_tbl,
                                    PurchaseOrders_tbl.EmployeeID
                                    == Employees_tbl.EmployeeID,
                                )
                                .where(
                                    PurchaseOrders_tbl.PoID == PoID,
                                )
                            )
                            answ_check_po_Employees_tbl = (
                                session_po.execute(stmt_check_po_Employees_tbl)
                                .mappings()
                                .all()
                            )
                            if answ_check_po_Employees_tbl:
                                SalesFirstName = answ_check_po_Employees_tbl[0][
                                    "SalesFirstName"
                                ]
                            else:
                                SalesFirstName = "No data"
                            # PO quantities are NOT added to qty_list (excluded from total)
                            temp_po_inprogress = {
                                "Number": PoNumber,
                                "Type": "PO",
                                "QuotationDate": i["PoDate"].strftime("%m-%d-%Y"),
                                "SalesFirstName": SalesFirstName,
                                "AccountNo": i["AccountNo"],
                                "BinLocations": bin_locations_display,
                                "Packer": "No data",
                                "Dop2Time": "--",
                                "Dop3Time": "--",
                                "QTY": i["QtyOrdered"],
                            }
                            po_inventory_inprogress.append(temp_po_inprogress)

                if sum(qty_list) != 0:
                    update_inventory_inprogress.append(
                        {"Total_inprogress": sum(qty_list)}
                    )
            model = self._find_model_from_identity("manualinventoryupdate")
            config_model = await model._configs(request)
            if form.get("_update_inventory", None) is not None:
                if ProductDescription:
                    with Session(engine["DB1"]) as session:
                        stmt_Items_tbl = select(
                            Items_tbl.__table__.columns,
                        ).where(
                            and_(
                                Items_tbl.ProductDescription
                                == dict_obj["ProductDescription"],
                                Items_tbl.Discontinued == 0,
                            )
                        )
                        answ_Items_tbl = (
                            session.execute(stmt_Items_tbl).mappings().all()
                        )
                        dict_obj.update({"Qty": answ_Items_tbl[0]["QuantOnHand"]})
                        dict_obj.update({"ProductID": answ_Items_tbl[0]["ProductID"]})
                        dict_obj.update({"ProductUPC": answ_Items_tbl[0]["ProductUPC"]})
                newQty = dict_obj["newQty"]
                if newQty != None and (
                    checking_str(newQty) == "str" or checking_str(newQty) == "float"
                ):
                    errors_update_inventory = "New Qty must be integer"
                    response = self.templates.TemplateResponse(
                        "manualupdate.html",
                        {
                            "request": request,
                            "model": model,
                            "obj": dict_obj,
                            "update": update_inventory,
                            "update_error": errors_update_inventory,
                            "bin_locations": bin_locations_display,
                            "po_inprogress": po_inventory_inprogress,
                            "menu": menu(request),
                        },
                    )
                    response.headers["Cache-Control"] = (
                        "no-store, no-cache, must-revalidate, max-age=0"
                    )
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
            if (
                not check_none(dict_obj)
                and dict_obj["newQty"]
                and dict_obj["ProductDescription"]
                and dict_obj["SKU"]
            ):
                ProductID = dict_obj["ProductID"]
                ProductDescription = dict_obj["ProductDescription"]
                ProductSKU = dict_obj["SKU"]
                ProductUPC = dict_obj["ProductUPC"]
                old_qty = int(dict_obj["Qty"])
                us_qty = int(dict_obj["newQty"])
                new_qty = int(us_qty)
                with Session(engine["DB1"]) as session:

                    stmt_ch_Items_tbl = select(
                        Items_tbl.__table__.columns,
                    ).where(Items_tbl.ProductID == ProductID)
                    answ_ch_Items_tbl = (
                        session.execute(stmt_ch_Items_tbl).mappings().all()
                    )
                    if answ_ch_Items_tbl[0]["ReorderLevel"] == 9:
                        stmt_update_items = (
                            update(Items_tbl)
                            .values(QuantOnHand=new_qty)
                            .where(Items_tbl.ProductID == ProductID)
                        )
                    else:
                        stmt_update_items = (
                            update(Items_tbl)
                            .values(
                                ReorderLevel=7,
                                QuantOnHand=new_qty,
                            )
                            .where(Items_tbl.ProductID == ProductID)
                        )
                    rows_update_items = session.execute(stmt_update_items)
                    session.commit()
                with Session(engine["DB_admin"]) as session1:
                    stmt_ManualInventoryUpdate = (
                        insert(ManualInventoryUpdate)
                        .values(
                            DateCreated=time_now_5h_min,
                            Username=user_account,
                            UserStatus=statususer,
                            UpdateType="Inventory",
                            ProductSKU=ProductSKU,
                            ProductUPC=ProductUPC,
                            ProductDescription=ProductDescription.replace("'", "''"),
                            OldQty=old_qty,
                            NewQty=new_qty,
                            DiffQty=new_qty - old_qty,
                        )
                        .returning(
                            ManualInventoryUpdate.id,
                        )
                    )
                    rows_ManualInventoryUpdate = (
                        session1.execute(stmt_ManualInventoryUpdate).mappings().all()
                    )
                    session1.commit()
                with Session(engine["DB1"]) as session:
                    stmt_Items_tbl = select(
                        Items_tbl.__table__.columns,
                    ).where(Items_tbl.ProductID == ProductID)
                    answ_Items_tbl = session.execute(stmt_Items_tbl).mappings().all()
                    dict_obj.update({"Qty": answ_Items_tbl[0]["QuantOnHand"]})
                    dict_obj.update({"newQty": None})
                update_inventory = f'Item "{ProductDescription}", UPC: "{ProductUPC}" update successful, New Qty: {new_qty}'
            response = self.templates.TemplateResponse(
                "manualupdate.html",
                {
                    "request": request,
                    "model": model,
                    "obj": dict_obj,
                    "update": update_inventory,
                    "inprogress": update_inventory_inprogress,
                    "po_inprogress": po_inventory_inprogress,
                    "bin_locations": bin_locations_display,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

        elif identity_req == "purchaseorder":
            model = self._find_model_from_identity("purchaseorder")
            config_model = await model._configs(request)
            response = self.templates.TemplateResponse(
                "po_list.html",
                {
                    "request": request,
                    "model": model,
                    "__js_model__": config_model,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif identity_req == "createpurchaseorder":
            model = self._find_model_from_identity("createpurchaseorder")
            config_model = await model._configs(request)
            response = self.templates.TemplateResponse(
                "create_edit_po.html",
                {
                    "request": request,
                    "model": model,
                    "__js_model__": config_model,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif identity_req == "items_massupdate":
            list_obj_detail: list[str] = list()
            model = self._find_model_from_identity("items_massupdate")
            get_all_actions = await model.get_all_actions(request)
            config_model = await model._configs(request)
            response = self.templates.TemplateResponse(
                "items_massupdate.html",
                {
                    "request": request,
                    "model": model,
                    "__js_model__": config_model,
                    "obj": {},
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif identity_req == "settings":
            if "admin" not in statususer.split("/"):
                # logic for non-admin users
                response = self.templates.TemplateResponse(
                    "settings.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": {},
                        "update_error": 0,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            else:
                # logic for admin users
                response = self.templates.TemplateResponse(
                    "settings.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": {},
                        "update_error": 0,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        elif identity_req == "orderslock":
            list_obj_detail: list[str] = list()
            model = self._find_model_from_identity("orderslock")
            get_all_actions = await model.get_all_actions(request)
            config_model = await model._configs(request)
            form = await request.form()
            user_account = request.state.user
            print(user_account, "user_accounttttttttsss")
            errors_update_inventory = ""
            update_inventory = ""
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            if form.get("_update_lock", None) is not None:
                if "checker" not in statususer.split("/"):
                    response = self.templates.TemplateResponse(
                        "orderslock.html",
                        {
                            "request": request,
                            "model": model,
                            "obj": {},
                            "update_error": "Error: Your user must have Checker-Role",
                            "menu": menu(request),
                        },
                    )
                    response.headers["Cache-Control"] = (
                        "no-store, no-cache, must-revalidate, max-age=0"
                    )
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
                data_lock = form.get("orderslock")
                if not data_lock:
                    errors_update_inventory = f"Scan Quotation bar code first"
                    response = self.templates.TemplateResponse(
                        "orderslock.html",
                        {
                            "request": request,
                            "model": model,
                            "obj": {},
                            "update_error": errors_update_inventory,
                            "menu": menu(request),
                        },
                    )
                    response.headers["Cache-Control"] = (
                        "no-store, no-cache, must-revalidate, max-age=0"
                    )
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
                if "&" not in data_lock:
                    response = self.templates.TemplateResponse(
                        "orderslock.html",
                        {
                            "request": request,
                            "model": model,
                            # "__js_model__": config_model,
                            "obj": {},
                            "update_error": "Just don’t enter any nonsense into this field! :)) Scan the barcode and that's it!",
                            "update": update_inventory,
                            "menu": menu(request),
                        },
                    )
                    response.headers["Cache-Control"] = (
                        "no-store, no-cache, must-revalidate, max-age=0"
                    )
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
                QuotationID = data_lock.split("&")[0]
                SourceDB = engine_db_nick_name[data_lock.split("&")[1]]
                with Session(engine["DB_admin"]) as session:
                    stmt_QS = select(
                        QuotationsStatus.__table__.columns,
                    ).where(QuotationsStatus.Dop1 == QuotationID)
                    answ_QS = session.execute(stmt_QS).mappings().all()
                    if answ_QS:
                        QuotationNumber = answ_QS[0]["QuotationNumber"]
                        stmt_update_qs = (
                            update(QuotationsStatus)
                            .values(
                                LastUpdate=time_now_5h,
                                Status="LOCKED",
                                Checker=user_account["name"],
                            )
                            .where(QuotationsStatus.Dop1 == QuotationID)
                        )
                        answ_update_qs = session.execute(stmt_update_qs)
                        stmt_update_qis = (
                            update(QuotationsInProgress)
                            .values(
                                Status="LOCKED",
                                Checker=user_account["name"],
                            )
                            .where(
                                and_(
                                    QuotationsInProgress.tempField1 == QuotationID,
                                    QuotationsInProgress.SourceDB == SourceDB,
                                )
                            )
                        )
                        answ_update_qis = session.execute(stmt_update_qis)
                        session.commit()
                        if answ_QS[0]["Status"] == "LOCKED":
                            errors_update_inventory = (
                                f"Quotation: {QuotationNumber} already locked"
                            )
                        else:
                            update_inventory = (
                                f"Quotation: {QuotationNumber} successfully locked"
                            )
                    else:
                        errors_update_inventory = f"This Quotation: {QuotationNumber} cannot be locked, because it was not created through this application."
            response = self.templates.TemplateResponse(
                "orderslock.html",
                {
                    "request": request,
                    "model": model,
                    "obj": {},
                    "update_error": errors_update_inventory,
                    "update": update_inventory,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif identity_req == "reports":
            list_obj_detail: list[str] = list()
            dict_obj = await self.form_to_dict(
                request, form, model, RequestAction.CREATE
            )
            model = self._find_model_from_identity("reports")
            get_all_actions = await model.get_all_actions(request)
            config_model = await model._configs(request)
            form = await request.form()
            user_account = request.state.user
            errors_update_inventory = ""
            update_inventory = ""
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            if dict_obj["DateFrom"] != None and dict_obj["DateTo"] != None:
                dict_obj.update({"DateFrom": dict_obj["DateFrom"].strftime("%Y-%m-%d")})
                dict_obj.update({"DateTo": dict_obj["DateTo"].strftime("%Y-%m-%d")})
            else:
                response = self.templates.TemplateResponse(
                    "repo.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": dict_obj,
                        "update_error": "Enter 'Date From' and 'Date To'",
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            if form.get("_cr_rep", None) is not None:
                headers = {
                    "Content-type": "application/json",
                    "accept": "application/json",
                }
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"http://{sr}/repincheck/",
                        data=json.dumps(dict_obj, indent=4),
                        headers=headers,
                        timeout=None,
                    )
                ans = json.loads(response.text)
                response = self.templates.TemplateResponse(
                    "repo.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": dict_obj,
                        "data_table": ans,
                        # "update": update_inventory,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            response = self.templates.TemplateResponse(
                "repo.html",
                {
                    "request": request,
                    "model": model,
                    "obj": {},
                    "update_error": errors_update_inventory,
                    "update": update_inventory,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        if form.get("_update_prod", None) is not None:
            dict_obj1 = copy.deepcopy(dict_obj)
            if dict_obj1["Prodtempl1"] != None:
                query_prod1 = f"select * from Items_tbl Where ProductID = {dict_obj1[f'Prodtempl1']}"
                answ_prod1 = pd_req(query_prod1, "DB1")
                dict_obj.update(
                    {"ProductDescription": answ_prod1[0]["ProductDescription"]}
                )
                dict_obj.update({"ProductSKU": str(answ_prod1[0]["ProductSKU"])})
                dict_obj.update({"ItemSize": str(answ_prod1[0]["ItemSize"])})
                dict_obj.update({"ItemWeight": str(answ_prod1[0]["ItemWeight"])})
                dict_obj.update({"CountInUnit": str(answ_prod1[0]["CountInUnit"])})
                product_upc = answ_prod1[0]["ProductUPC"]
                for i in ["Prodtempl2", "Prodtempl3"]:
                    if dict_obj1[i] == None:
                        query_invoice_UPC = f"select * from Items_tbl Where ProductUPC = '{product_upc}'"
                        answ_invoice_UPC = pd_req(query_invoice_UPC, f"DB{i[-1]}")
                        if answ_invoice_UPC:
                            if len(answ_invoice_UPC) > 1:
                                for i1 in range(len(answ_invoice_UPC)):
                                    if answ_invoice_UPC[i1]["Discontinued"] == False:
                                        dict_obj.update(
                                            {i: str(answ_invoice_UPC[i1]["ProductID"])}
                                        )
                            else:
                                dict_obj.update(
                                    {i: str(answ_invoice_UPC[0]["ProductID"])}
                                )
            elif dict_obj1["Prodtempl4"] != None:
                query_prod1 = f"select * from Items_tbl Where ProductID = {dict_obj1[f'Prodtempl4']}"
                answ_prod1 = pd_req(query_prod1, "DB4")
                dict_obj.update(
                    {"ProductDescription": answ_prod1[0]["ProductDescription"]}
                )
                dict_obj.update({"ProductSKU": str(answ_prod1[0]["ProductSKU"])})
                dict_obj.update({"ItemSize": str(answ_prod1[0]["ItemSize"])})
                dict_obj.update({"ItemWeight": str(answ_prod1[0]["ItemWeight"])})
                dict_obj.update({"CountInUnit": str(answ_prod1[0]["CountInUnit"])})
                product_upc = answ_prod1[0]["ProductUPC"]
                for i in ["Prodtempl2", "Prodtempl3"]:
                    if dict_obj1[i] == None:
                        query_invoice_UPC = f"select * from Items_tbl Where ProductUPC = '{product_upc}'"
                        answ_invoice_UPC = pd_req(query_invoice_UPC, f"DB{i[-1]}")
                        if answ_invoice_UPC:
                            if len(answ_invoice_UPC) > 1:
                                for i1 in range(len(answ_invoice_UPC)):
                                    if answ_invoice_UPC[i1]["Discontinued"] == False:
                                        dict_obj.update(
                                            {i: str(answ_invoice_UPC[i1]["ProductID"])}
                                        )
                            else:
                                dict_obj.update(
                                    {i: str(answ_invoice_UPC[0]["ProductID"])}
                                )
            product_id_dict = {}
            for i in dict_obj1:
                if "Prodtempl" in i and dict_obj[i] != None:
                    product_id_dict[i] = dict_obj[f"Prodtempl{i[-1]}"]
                    req_db = f"DB{i[-1]}"
                    query_invoice_dest = f"select * from Items_tbl Where ProductID = {dict_obj[f'Prodtempl{i[-1]}']}"
                    answ_invoice_query = pd_req(query_invoice_dest, req_db)
                    dict_obj.update({i: answ_invoice_query[0]["ProductDescription"]})
            if product_id_dict:
                for i in product_id_dict:
                    product_id = product_id_dict[i]
                    req_db = f"DB{i[-1]}"
                    query_UnitCost = (
                        f"select UnitCost from Items_tbl Where ProductID = {product_id}"
                    )
                    answ_UnitCost = pd_req(query_UnitCost, req_db)
                    if answ_UnitCost:
                        dict_obj.update(
                            {f"UnitCost{i[-1]}": answ_UnitCost[0]["UnitCost"]}
                        )
                    query_UnitPrice = f"select UnitPrice from Items_tbl Where ProductID = {product_id}"
                    answ_UnitPrice = pd_req(query_UnitPrice, req_db)
                    if answ_UnitPrice:
                        dict_obj.update(
                            {f"UnitPrice{i[-1]}1": f'${answ_UnitPrice[0]["UnitPrice"]}'}
                        )
                    query_ManuID = (
                        f"select ManuID from Items_tbl Where ProductID = {product_id}"
                    )
                    answ_ManuID = pd_req(query_ManuID, req_db)
                    if answ_ManuID and answ_ManuID[0]["ManuID"] != 0:
                        query_Manuname = f'select ManuName from Manufacturers_tbl Where ManufacturerID = {answ_ManuID[0]["ManuID"]}'
                        try:
                            answ_Manuname = pd_req(query_Manuname, req_db)
                            if answ_Manuname:
                                dict_obj.update(
                                    {f"ManuID{i[-1]}": answ_Manuname[0]["ManuName"]}
                                )
                            else:
                                dict_obj.update({f"ManuID{i[-1]}": None})
                        except exc_sqlalchemy.ProgrammingError:
                            dict_obj.update({f"ManuID{i[-1]}": None})

                    query_UnitID = (
                        f"select UnitID from Items_tbl Where ProductID = {product_id}"
                    )
                    answ_UnitID = pd_req(query_UnitID, req_db)
                    if answ_UnitID and answ_UnitID[0]["UnitID"] != 0:
                        query_UnitID = f'select UnitDesc from Units_tbl Where UnitID = {answ_UnitID[0]["UnitID"]}'
                        try:
                            answ_UnitID1 = pd_req(query_UnitID, req_db)
                            if answ_UnitID1:
                                dict_obj.update(
                                    {f"UnitID{i[-1]}1": answ_UnitID1[0]["UnitDesc"]}
                                )
                            else:
                                dict_obj.update({f"UnitID{i[-1]}1": None})
                        except exc_sqlalchemy.ProgrammingError:
                            dict_obj.update({f"UnitID{i[-1]}1": None})

                    query_TaxID = f"select ItemTaxID from Items_tbl Where ProductID = {product_id}"
                    answ_TaxID = pd_req(query_TaxID, req_db)
                    if answ_TaxID and answ_TaxID[0]["ItemTaxID"] != 0:
                        query_TaxID = f'select TaxName from ItemTaxes_tbl Where TaxID = {answ_TaxID[0]["ItemTaxID"]}'
                        try:
                            answ_TaxID1 = pd_req(query_TaxID, req_db)
                            if answ_TaxID1:
                                dict_obj.update(
                                    {f"TaxID{i[-1]}1": answ_TaxID1[0]["TaxName"]}
                                )
                            else:
                                dict_obj.update({f"TaxID{i[-1]}1": None})
                        except exc_sqlalchemy.ProgrammingError:
                            dict_obj.update({f"TaxID{i[-1]}1": None})
                    query_CateID = f"SELECT SubCateName FROM SubCategories_tbl INNER JOIN Items_tbl \
                             ON SubCategories_tbl.SubCateID = Items_tbl.SubCateID WHERE Items_tbl.ProductID = {product_id}"
                    answ_CateID = pd_req(query_CateID, req_db)
                    if answ_CateID:
                        dict_obj.update(
                            {f"CateID{i[-1]}": answ_CateID[0]["SubCateName"]}
                        )
                    else:
                        dict_obj.update({f"CateID{i[-1]}": None})
        elif form.get("_load_query", None) is not None:
            query_request = request.__dict__["_form"]["QUERY"]
            try:
                obj = await model.create_load_query(request, dict_obj)
                query_alias = f"select data from admin_query Where alias = '{dict_obj['queryalias']}'"
                answ_query_alias = pd_req(query_alias, "DB_admin")[0]["data"]
                dict_obj.update({"QUERY": answ_query_alias})
                response = self.templates.TemplateResponse(
                    "create_invoices.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            except FormValidationError as exc:
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "errors": exc.errors,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        elif form.get("_save_query", None) is not None:
            try:
                obj = await model.create_save_query(request, dict_obj)
                queryname_save_query = dict_obj["queryname"]
                with Session(engine["DB_admin"]) as session:
                    stmt_select_insert_alias = select(
                        admin_query.__table__.columns
                    ).filter_by(alias=queryname_save_query)
                    answ_select_insert_alias = (
                        session.execute(stmt_select_insert_alias).mappings().all()
                    )
                    if (
                        answ_select_insert_alias
                        and answ_select_insert_alias[0]["alias"] == queryname_save_query
                    ):
                        stmt_update_items = (
                            update(admin_query)
                            .values(data=dict_obj["QUERY"])
                            .where(admin_query.alias == queryname_save_query)
                        )
                        rows = session.execute(stmt_update_items)
                    else:
                        query_insert_alias = insert(admin_query).values(
                            alias=queryname_save_query,
                            data=dict_obj["QUERY"],
                        )
                        answ_insert_alias = session.execute(query_insert_alias)
                    session.commit()
            except FormValidationError as exc:
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "errors": exc.errors,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            response = self.templates.TemplateResponse(
                "create_invoices.html",
                {
                    "request": request,
                    "model": model,
                    "update": f'Query: {dict_obj["queryname"]} Successfully Added',
                    "obj": dict_obj,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif form.get("_reserve_quotation", None) is not None:
            try:
                obj = await model.create_reserve_quotation(request, dict_obj)
                quotation_number = dict_obj["quotation"]
                with Session(engine[dict_obj["choicedb_source"]]) as session:
                    query_quotation = select(
                        Quotations_tbl.__table__.columns
                    ).filter_by(QuotationNumber=quotation_number)
                    answ_quotation_number = (
                        session.execute(query_quotation).mappings().all()
                    )
                    if not answ_quotation_number:
                        query_quotation = select(
                            Quotations_tbl.__table__.columns
                        ).filter_by(AutoOrderNo=quotation_number)
                        answ_quotation_number = (
                            session.execute(query_quotation).mappings().all()
                        )
                    if answ_quotation_number:
                        reserve_QuotationID = answ_quotation_number[0]["QuotationID"]
                        reserve_QuotationNumber = answ_quotation_number[0][
                            "QuotationNumber"
                        ]
                        reserve_AutoOrderNo = answ_quotation_number[0]["AutoOrderNo"]
                        BusinessName = answ_quotation_number[0]["BusinessName"]

                        if reserve_AutoOrderNo and reserve_AutoOrderNo != None:
                            quotation_number = reserve_AutoOrderNo
                    else:
                        errors = {
                            "quotation": f'This Quotation or Invoice Number is not present in the Database: {SEARCH_IN_DICT_VALUE_RETURN_KEY(engine_nick, dict_obj["choicedb_source"])}'
                        }
                        raise FormValidationError(errors)
                    with Session(engine["DB_admin"]) as session1:
                        if reserve_AutoOrderNo and reserve_AutoOrderNo != None:
                            query_check = select(Quotation).filter_by(
                                InvoiceNumber=reserve_AutoOrderNo
                            )
                        else:
                            query_check = select(Quotation).filter_by(
                                QuotationNumber=reserve_QuotationNumber
                            )

                        rows = session1.execute(query_check).mappings().all()
                        if rows:
                            errors = {"quotation": "This quotation is already create"}
                            raise FormValidationError(errors)

                    def no_details(answ: str | None):
                        if not answ:
                            errors = {
                                "quotation": f"No details for: {quotation_number}"
                            }
                            raise FormValidationError(errors)

                    if quotation_number == reserve_QuotationNumber:
                        query_employees = f"SELECT FirstName FROM Employees_tbl INNER JOIN Quotations_tbl ON Employees_tbl.EmployeeID = Quotations_tbl.SalesRepID \
                                                WHERE Quotations_tbl.QuotationNumber = '{quotation_number}'"
                        answ_employees = pd_req(
                            query_employees, dict_obj["choicedb_source"]
                        )[0]["FirstName"]
                        query_quotationdetails = f"select * from QuotationsDetails_tbl Where QuotationID = {reserve_QuotationID}"
                        answ_quotationdetails = pd_req(
                            query_quotationdetails, dict_obj["choicedb_source"]
                        )
                        no_details(answ_quotationdetails)
                        quotationdetails_dict = dict(
                            (i["ProductUPC"], i["Qty"]) for i in answ_quotationdetails
                        )
                        quotationdetails_all_dict = dict(
                            (i["ProductUPC"], i) for i in answ_quotationdetails
                        )
                        quotationdetails_descr_dict = dict(
                            (i["ProductUPC"], i["ProductDescription"])
                            for i in answ_quotationdetails
                        )
                        quotation_dict = dict(
                            (i["QuotationID"], i) for i in answ_quotation_number
                        )
                    elif quotation_number == reserve_AutoOrderNo:
                        query_employees = f"SELECT FirstName FROM Employees_tbl INNER JOIN Quotations_tbl ON Employees_tbl.EmployeeID = Quotations_tbl.SalesRepID \
                                                WHERE Quotations_tbl.AutoOrderNo = '{quotation_number}'"
                        answ_employees = (
                            pd_req(query_employees, dict_obj["choicedb_source"])[0][
                                "FirstName"
                            ]
                            .strip()
                            .lower()
                        )
                        stmt_autoorder = (
                            select(InvoicesDetails_tbl, Invoices_tbl.BusinessName)
                            .join(
                                Invoices_tbl,
                                InvoicesDetails_tbl.InvoiceID == Invoices_tbl.InvoiceID,
                            )
                            .where(Invoices_tbl.InvoiceNumber == reserve_AutoOrderNo)
                        )
                        answ_quotationdetails_temp = (
                            session.execute(stmt_autoorder).mappings().all()
                        )
                        no_details(answ_quotationdetails_temp)
                        answ_quotationdetails = [
                            i["InvoicesDetails_tbl"].__dict__
                            for i in answ_quotationdetails_temp
                        ]
                        quotationdetails_dict = dict(
                            (i["ProductUPC"], i["QtyShipped"])
                            for i in answ_quotationdetails
                            if i["ProductUPC"] != None
                        )
                        quotationdetails_all_dict = dict(
                            (i["ProductUPC"], i)
                            for i in answ_quotationdetails
                            if i["ProductUPC"] != None
                        )
                        quotationdetails_descr_dict = dict(
                            (i["ProductUPC"], i["ProductDescription"])
                            for i in answ_quotationdetails
                            if i["ProductUPC"] != None
                        )
                        quotation_dict = dict(
                            (i["QuotationID"], i) for i in answ_quotation_number
                        )
                quotationdetails_dest_dict: Dict[int, int] = {}
                quotationdetails_dest_error_dict: Dict[int, int] = {}
                quotationdetails_dest_error_list = []
                answ_quotation_items_dict = {}
                for i in quotationdetails_dict:
                    query_quotation_items = (
                        f"select QuantOnHand from Items_tbl Where ProductUPC = '{i}'"
                    )
                    answ_quotation_items = pd_req(query_quotation_items, "DB1")
                    if answ_quotation_items:
                        for i1 in range(len(answ_quotation_items)):
                            quotationdetails_dest_dict[i] = (
                                answ_quotation_items[i1]["QuantOnHand"]
                                - quotationdetails_dict[i]
                            )
                    else:
                        quotationdetails_dest_error_list.append(
                            f"Not added -- Description: {quotationdetails_descr_dict[i]} UPC: {i} Quantity: {quotationdetails_dict[i]}"
                        )
                if not quotationdetails_dest_dict:
                    errors = {
                        "quotation": f'No one products are in the database: {dict_obj["choicedb_source"]}'
                    }
                    raise FormValidationError(errors)
                quotationdetails_dest_error_str = ""
                for i2 in quotationdetails_dest_error_dict:
                    quotationdetails_dest_error_str = (
                        quotationdetails_dest_error_str
                        + f"UPC: {i2} Quantity: {quotationdetails_dest_error_dict[i2]}\n"
                    )
                with Session(engine["DB1"]) as session:
                    for i in quotationdetails_dest_dict:
                        if quotationdetails_dest_dict[i] < 0:
                            quotationdetails_dest_error_list.append(
                                f"Оut of stock -- Description: {quotationdetails_descr_dict[i]} UPC: {i} Quantity: {quotationdetails_dest_dict[i]}"
                            )
                with Session(engine["DB_admin"]) as session:
                    Description = quotationdetails_all_dict[i]["ProductDescription"]
                    SalesRepresentative = answ_employees
                    time_now = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                    time_now_5h = (
                        datetime.datetime.today() - datetime.timedelta(hours=5)
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    if reserve_AutoOrderNo and reserve_AutoOrderNo != None:
                        stmt = insert(Quotation).values(
                            QuotationNumber=reserve_QuotationNumber,
                            SalesRepresentative=SalesRepresentative.replace("'", "''"),
                            BusinessName=BusinessName.replace("'", "''"),
                            Description=Description.replace("'", "''"),
                            Status="RESERVED",
                            DateCreate=time_now_5h,
                            LastUpdate=time_now_5h,
                            SourceDB=SEARCH_IN_DICT_VALUE_RETURN_KEY(
                                engine_nick, dict_obj["choicedb_source"]
                            ),
                            InvoiceNumber=reserve_AutoOrderNo,
                            FlagOrder=True,
                        )
                    else:
                        stmt = insert(Quotation).values(
                            QuotationNumber=reserve_QuotationNumber,
                            SalesRepresentative=SalesRepresentative.replace("'", "''"),
                            BusinessName=BusinessName.replace("'", "''"),
                            Description=Description.replace("'", "''"),
                            Status="RESERVED",
                            DateCreate=time_now_5h,
                            LastUpdate=time_now_5h,
                            SourceDB=SEARCH_IN_DICT_VALUE_RETURN_KEY(
                                engine_nick, dict_obj["choicedb_source"]
                            ),
                            FlagOrder=False,
                        )
                    rows = session.execute(stmt).mappings().all()
                    for i in quotationdetails_dest_dict:
                        ProductDescription = quotationdetails_descr_dict[i]
                        QTY = quotationdetails_dict[i]
                        ProductSKU = quotationdetails_all_dict[i]["ProductSKU"]
                        ProductUPC = quotationdetails_all_dict[i]["ProductUPC"]
                        if reserve_AutoOrderNo and reserve_AutoOrderNo != None:
                            stmt = insert(QuotationDetails).values(
                                QuotationNumber=reserve_QuotationNumber,
                                ProductDescription=ProductDescription,
                                ProductSKU=ProductSKU,
                                ProductUPC=ProductUPC,
                                QTY=QTY * -1,
                                InvoiceNumber=reserve_AutoOrderNo,
                                FlagOrder=True,
                            )
                        else:
                            stmt = insert(QuotationDetails).values(
                                QuotationNumber=reserve_QuotationNumber,
                                ProductDescription=ProductDescription,
                                ProductSKU=ProductSKU,
                                ProductUPC=ProductUPC,
                                QTY=QTY * -1,
                                FlagOrder=False,
                            )
                        rows = session.execute(stmt).mappings().all()
                    session.commit()
            except FormValidationError as exc:
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "errors": exc.errors,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            response = self.templates.TemplateResponse(
                "create_quotation.html",
                {
                    "request": request,
                    "model": model,
                    "update": f"Successfully Update",
                    "update_error_list": quotationdetails_dest_error_list,
                    "obj": dict_obj,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif form.get("_add_items_quotation", None) is not None:
            try:
                obj = await model.add_items_quotation(request, dict_obj)
                quotation_number = dict_obj["quotation"]
                with Session(engine[dict_obj["choicedb_source"]]) as session:
                    query_quotation = select(
                        Quotations_tbl.__table__.columns
                    ).filter_by(QuotationNumber=quotation_number)
                    answ_quotation_number = (
                        session.execute(query_quotation).mappings().all()
                    )
            except FormValidationError as exc:
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "errors": exc.errors,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            response = self.templates.TemplateResponse(
                "create_quotation.html",
                {
                    "request": request,
                    "model": model,
                    "update": f"Successfully Update",
                    "update_error_list": quotationdetails_dest_error_list,
                    "obj": dict_obj,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif form.get("add_quotation", None) is not None:
            model = self._find_model_from_identity("quotationsdetails1_tbl")
            get_all_actions = await model.get_all_actions(request)
            config_model = await model._configs(request)
        elif form.get("_checkdb_quotation", None) is not None:
            model11 = self._find_model_from_identity("quotations1_tbl")
            get_all_actions = await model11.get_all_actions(request)
            config_model = await model11._configs(request)
            if "qty" in dict_obj:
                dict_obj1 = copy.deepcopy(dict_obj)
                if dict_obj1["qty"].isdigit():
                    dict_obj.update({"qty": int(dict_obj1["qty"])})
            dict_obj.update({"Total": "Total"})
            check_dict_obj_list = [
                i for i in dict_obj if dict_obj[i] == None or not dict_obj[i]
            ]
            if check_dict_obj_list:
                response = self.templates.TemplateResponse(
                    "create_new_quotation.html",
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            elif (
                not dict_obj["QTY"].isdigit()
                or not dict_obj["Price"].replace(".", "0").isdigit()
            ):
                response = self.templates.TemplateResponse(
                    "create_new_quotation.html",
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "update_error": "QTY must be integer and Price must be float",
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            elif not check_dict_obj_list and int(dict_obj["QTY"]) <= 0:
                response = self.templates.TemplateResponse(
                    "create_new_quotation.html",
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": dict_obj,
                        "update_error": "QTY must be greater than zero.",
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            with Session(engine["DB_admin"]) as session:
                query_quotation_temp = select(
                    QuotationsTemp.__table__.columns
                ).filter_by(SessionID=user_account)
                answ_quotation_temp = (
                    session.execute(query_quotation_temp).mappings().all()
                )
                list_sku_quotation_temp: List[str] = [
                    i["SKU"] for i in answ_quotation_temp
                ]
                if answ_quotation_temp:
                    if answ_quotation_temp[0]["SourceDB"] != dict_obj["SourceDB"]:
                        response = self.templates.TemplateResponse(
                            "create_new_quotation.html",
                            {
                                "request": request,
                                "model": model,
                                "_actions": get_all_actions,
                                "__js_model__": config_model,
                                "obj": dict_obj,
                                "update_error": f"""You can't change Database: {answ_quotation_temp[0]['SourceDB']} in this session.
                                If you want change Database, press the button Clear and start the process again.""",
                                "menu": menu(request),
                            },
                        )
                        response.headers["Cache-Control"] = (
                            "no-store, no-cache, must-revalidate, max-age=0"
                        )
                        response.headers["Pragma"] = "no-cache"
                        response.headers["Expires"] = "0"
                        return response
                    elif answ_quotation_temp[0]["AccountNo"] != dict_obj["AccountNo"]:

                        response = self.templates.TemplateResponse(
                            "create_new_quotation.html",
                            {
                                "request": request,
                                "model": model,
                                "_actions": get_all_actions,
                                "__js_model__": config_model,
                                "obj": dict_obj,
                                "update_error": f"""You can't change Business Name: {answ_quotation_temp[0]['BusinessName']} in this session.
                                If you want change Business Name, press the button Clear and start the process again.""",
                                "menu": menu(request),
                            },
                        )
                        response.headers["Cache-Control"] = (
                            "no-store, no-cache, must-revalidate, max-age=0"
                        )
                        response.headers["Pragma"] = "no-cache"
                        response.headers["Expires"] = "0"
                        return response
                    elif dict_obj["SKU"] in list_sku_quotation_temp:
                        response = self.templates.TemplateResponse(
                            "create_new_quotation.html",
                            {
                                "request": request,
                                "model": model,
                                "_actions": get_all_actions,
                                "__js_model__": config_model,
                                "obj": dict_obj,
                                "update_error": f"""SKU: {dict_obj['SKU']} already present in this Quotation.
                                You can't duplicate SKUs.""",
                                "menu": menu(request),
                            },
                        )
                        response.headers["Cache-Control"] = (
                            "no-store, no-cache, must-revalidate, max-age=0"
                        )
                        response.headers["Pragma"] = "no-cache"
                        response.headers["Expires"] = "0"
                        return response
                stmt = (
                    insert(QuotationsTemp)
                    .values(
                        SessionID=user_account,
                        AccountNo=dict_obj["AccountNo"],
                        BusinessName=dict_obj["BusinessName"],
                        ProductDescription=dict_obj["ProductDescription"],
                        SKU=dict_obj["SKU"],
                        QTY=dict_obj["QTY"],
                        Price=dict_obj["Price"],
                        SourceDB=dict_obj["SourceDB"],
                        Total=int(dict_obj["QTY"]) * float(dict_obj["Price"]),
                    )
                    .returning(
                        QuotationsTemp.__table__.columns,
                    )
                )
                rows_quotation_status = session.execute(stmt).mappings().all()
                session.commit()
            dict_obj.pop("ProductDescription")
            dict_obj.pop("SKU")
            dict_obj.pop("QTY")
            dict_obj.pop("Price")

            response = self.templates.TemplateResponse(
                "create_new_quotation.html",
                {
                    "request": request,
                    "model": model,
                    "_actions": get_all_actions,
                    "__js_model__": config_model,
                    "obj": dict_obj,
                    "update": "Item Successfully Create",
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif form.get("_choose_db_quotation", None) is not None:
            model11 = self._find_model_from_identity("quotations2_tbl")
            form = await request.form()
            dict_obj = await self.form_to_dict(
                request, form, model11, RequestAction.CREATE
            )
            get_all_actions = await model11.get_all_actions(request)
            config_model = await model11._configs(
                request, dop=dict_obj["choicedb_source"]
            )

            response = self.templates.TemplateResponse(
                "list_all_quotation.html",
                {
                    "request": request,
                    "model": model,
                    "_actions": get_all_actions,
                    "__js_model__": config_model,
                    "obj": dict_obj,
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        elif form.get("_reset_session_quotation", None) is not None:
            model = self._find_model_from_identity("quotations1_tbl")
            get_all_actions = await model.get_all_actions(request)
            config_model = await model._configs(request)
            with Session(engine["DB_admin"]) as session1:
                stmt_delete = delete(QuotationsTemp).where(
                    QuotationsTemp.SessionID == user_account
                )
                answ_delete = session1.execute(stmt_delete)
                session1.commit()
                response = self.templates.TemplateResponse(
                    "create_new_quotation.html",
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": {},
                        "update": "Session Cleared",
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        elif form.get("edit_quotation", None) is not None:
            model = self._find_model_from_identity("quotationsdetails1_tbl")
            get_all_actions = await model.get_all_actions(request)
            config_model = await model._configs(request)
        elif form.get("_save_new_quotation", None) is not None:
            model = self._find_model_from_identity("quotations1_tbl")
            get_all_actions = await model.get_all_actions(request)
            config_model = await model._configs(request)
            with Session(engine["DB_admin"]) as session1:
                stmt_quotation_status = select(
                    QuotationsTemp.__table__.columns
                ).filter_by(SessionID=user_account)
                rows_quotation_status = (
                    session1.execute(stmt_quotation_status).mappings().all()
                )
                if not rows_quotation_status:
                    response = self.templates.TemplateResponse(
                        "create_new_quotation.html",
                        {
                            "request": request,
                            "model": model,
                            "_actions": get_all_actions,
                            "__js_model__": config_model,
                            "obj": dict_obj,
                            "update_error": "No one item for Quotation not created yet",
                            "menu": menu(request),
                        },
                    )
                    response.headers["Cache-Control"] = (
                        "no-store, no-cache, must-revalidate, max-age=0"
                    )
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
                stmt_quotation_total = select(func.sum(QuotationsTemp.Total)).filter_by(
                    SessionID=user_account
                )
                rows_quotation_total = (
                    session1.execute(stmt_quotation_total).mappings().all()
                )
                quotations_admin_total = rows_quotation_total[0]["sum"]
                SourceDB_admin = rows_quotation_status[0]["SourceDB"]
                AccountNo_admin = rows_quotation_status[0]["AccountNo"]
                with Session(engine[engine_nick[SourceDB_admin]]) as session:
                    new_number = generate_unique_quotation_number_simple(
                        session=session,
                        quotations_table=Quotations_tbl,
                    )

                    stmt_quotation_status = select(
                        Customers_tbl.__table__.columns
                    ).filter_by(AccountNo=AccountNo_admin)
                    answ_quotation_status = (
                        session.execute(stmt_quotation_status).mappings().all()
                    )
                    stmt_quotation_employees = select(
                        Employees_tbl.__table__.columns
                    ).where(func.lower(Employees_tbl.FirstName) == user_account)
                    rows_quotation_employees = (
                        session.execute(stmt_quotation_employees).mappings().all()
                    )

                    if not rows_quotation_employees:
                        SalesRepID = 0
                        SalesRepresentative = "undefined"
                        response = self.templates.TemplateResponse(
                            "create_new_quotation.html",
                            {
                                "request": request,
                                "model": model,
                                "_actions": get_all_actions,
                                "__js_model__": config_model,
                                "obj": dict_obj,
                                "update_error": "You cannot create Quotation. Your user is not present in Employees-Database",
                                "menu": menu(request),
                            },
                        )
                        response.headers["Cache-Control"] = (
                            "no-store, no-cache, must-revalidate, max-age=0"
                        )
                        response.headers["Pragma"] = "no-cache"
                        response.headers["Expires"] = "0"
                        return response
                    else:
                        SalesRepID = rows_quotation_employees[0]["EmployeeID"]
                        SalesRepresentative = rows_quotation_employees[0]["FirstName"]

                    ExpirationDate = (
                        datetime.datetime.today() + datetime.timedelta(days=10)
                    ).strftime("%Y-%m-%d 00:00:00")
                    time_now_5h = (
                        datetime.datetime.today() - datetime.timedelta(hours=5)
                    ).strftime("%Y-%m-%d %H:%M:%S")

                    stmt = (
                        insert(Quotations_tbl)
                        .values(
                            QuotationNumber=new_number,
                            ExpirationDate=ExpirationDate,
                            QuotationDate=time_now_5h,
                            CustomerID=answ_quotation_status[0]["CustomerID"],
                            BusinessName=answ_quotation_status[0]["BusinessName"],
                            AccountNo=answ_quotation_status[0]["AccountNo"],
                            Shipto=answ_quotation_status[0]["Shipto"],
                            ShipAddress1=answ_quotation_status[0]["Address1"],
                            ShipAddress2=answ_quotation_status[0]["Address2"],
                            ShipContact=answ_quotation_status[0]["ShipContact"],
                            ShipCity=answ_quotation_status[0]["ShipCity"],
                            ShipState=answ_quotation_status[0]["ShipState"],
                            ShipZipCode=answ_quotation_status[0]["ShipZipCode"],
                            ShipPhoneNo=answ_quotation_status[0]["Phone_Number"],
                            Status=1,
                            ShipperID=0,
                            flaged=0,
                            TermID=answ_quotation_status[0]["TermID"],
                            SalesRepID=SalesRepID,
                            QuotationTotal=quotations_admin_total,
                        )
                        .returning(
                            Quotations_tbl.QuotationID,
                        )
                    )
                    rows_quotation_insert = session.execute(stmt).mappings().all()
                    session.commit()
                    QuotationID = rows_quotation_insert[0]["QuotationID"]
                with Session(engine["DB_admin"]) as session1:
                    stmt_Quotation_admin = insert(Quotation).values(
                        QuotationNumber=int(answ_QuotationNumber) + 1,
                        SalesRepresentative=SalesRepresentative.replace("'", "''"),
                        BusinessName=answ_quotation_status[0]["BusinessName"].replace(
                            "'", "''"
                        ),
                        Description="",
                        Status="RESERVED",
                        DateCreate=time_now_5h,
                        LastUpdate=time_now_5h,
                        SourceDB=SourceDB_admin,
                        FlagOrder=False,
                    )

                    rows_Quotation_admin = (
                        session1.execute(stmt_Quotation_admin).mappings().all()
                    )
                    session1.commit()
                    for i in rows_quotation_status:
                        Qty = i["QTY"]
                        UnitPrice = i["Price"]
                        stmt_quotation_items = select(
                            Items_tbl.__table__.columns
                        ).filter_by(ProductSKU=i["SKU"])
                        rows_quotation_items = (
                            session.execute(stmt_quotation_items).mappings().all()
                        )
                        stmt_quotation_UnitDesc = select(
                            Units_tbl.__table__.columns
                        ).filter_by(UnitID=str(rows_quotation_items[0]["UnitID"]))
                        rows_quotation_UnitDesc = (
                            session.execute(stmt_quotation_UnitDesc).mappings().all()
                        )
                        if rows_quotation_UnitDesc:
                            UnitDesc = rows_quotation_UnitDesc[0]["UnitDesc"]
                        else:
                            UnitDesc = ""
                        stmt_quotationsdetails = (
                            insert(QuotationsDetails_tbl)
                            .values(
                                QuotationID=QuotationID,
                                CateID=rows_quotation_items[0]["CateID"],
                                SubCateID=rows_quotation_items[0]["SubCateID"],
                                ProductID=rows_quotation_items[0]["ProductID"],
                                ProductSKU=rows_quotation_items[0]["ProductSKU"],
                                ProductUPC=rows_quotation_items[0]["ProductUPC"],
                                ProductDescription=rows_quotation_items[0][
                                    "ProductDescription"
                                ],
                                ItemSize=rows_quotation_items[0]["ItemSize"],
                                ExpDate=ExpirationDate,
                                UnitPrice=UnitPrice,
                                OriginalPrice=UnitPrice,
                                UnitCost=rows_quotation_items[0]["UnitCost"],
                                Qty=Qty,
                                ItemWeight=rows_quotation_items[0]["ItemWeight"],
                                Discount=0,
                                ds_Percent=0,
                                ExtendedPrice=UnitPrice * Qty,
                                ExtendedCost=rows_quotation_items[0]["UnitCost"] * Qty,
                                ExtendedDisc=0,
                                PromotionID=0,
                                PromotionLine=0,
                                SPPromoted=0,
                                Taxable=0,
                                ItemTaxID=0,
                                Catch=0,
                                Flag=0,
                                ActExtendedPrice=UnitPrice * Qty,
                                UnitDesc=UnitDesc,
                            )
                            .returning(
                                QuotationsDetails_tbl.LineID,
                            )
                        )
                        rows_quotationsdetails = (
                            session.execute(stmt_quotationsdetails).mappings().all()
                        )
                        stmt_QuotationDetails_admin = insert(QuotationDetails).values(
                            QuotationNumber=int(answ_QuotationNumber) + 1,
                            ProductDescription=rows_quotation_items[0][
                                "ProductDescription"
                            ],
                            ProductSKU=rows_quotation_items[0]["ProductSKU"],
                            ProductUPC=rows_quotation_items[0]["ProductUPC"],
                            QTY=Qty * -1,
                            FlagOrder=False,
                        )
                        rows_QuotationDetails_admin = (
                            session1.execute(stmt_QuotationDetails_admin)
                            .mappings()
                            .all()
                        )
                    session.commit()
                    session1.commit()

                stmt_delete = delete(QuotationsTemp).where(
                    QuotationsTemp.SessionID == user_account
                )
                answ_delete = session1.execute(stmt_delete)
                session1.commit()
            response = self.templates.TemplateResponse(
                "create_new_quotation.html",
                {
                    "request": request,
                    "model": model,
                    "_actions": get_all_actions,
                    "__js_model__": config_model,
                    "obj": {},
                    "url": "http://192.168.1.140/project/quotations1_tbl/list",
                    "update": "Successfully Updated",
                    "menu": menu(request),
                },
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        if "QUERY" in dict_obj:
            query_invoice = " ".join(dict_obj["QUERY"].split("\\n"))
            query_invoice = " ".join(query_invoice.split("\\r"))
            query_invoice = " ".join(query_invoice.split("\n"))
            query_invoice = " ".join(query_invoice.split("\r"))

            dict_obj.update({"QUERY": query_invoice})

        try:
            obj = await model.create1(request, dict_obj)
            print(obj)
            if obj[0] == "yes":

                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "obj": dict_obj,
                        "update_error": f"This SKU is already present in {obj[1]}",
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            if obj[0] == "dif_db":
                update_text = ""
                for item in obj[1]:
                    if item in DB_MAPPING:
                        update_text += f"{DB_MAPPING[item]}, "
                try:
                    update_text = update_text.rstrip(", ")
                except:
                    update_text = obj[1]
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "update": f"Successfully Create in {update_text}",
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            elif obj[0] == "ok":
                obj_detail = obj[1]
                response = self.templates.TemplateResponse(
                    "create_new_quotation.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": obj_detail,
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            elif obj[0] == "create_new_quotation":
                model11 = self._find_model_from_identity("quotations1_tbl")
                get_all_actions = await model11.get_all_actions(request)
                print(get_all_actions, "get_all_actionsssssssss----======>>>>")
                config_model = await model11._configs(request)
                response = self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": obj[1],
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            elif obj[0] == "list_all_quotation":
                response = self.templates.TemplateResponse(
                    "list_all_quotation.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": obj[1],
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            elif obj[0] == "create_new_quotation_edit":
                response = self.templates.TemplateResponse(
                    "create_new_quotation_edit.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": obj[1],
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            elif obj[0] == "edit_quotation":
                query_update_quotation = dict(
                    parse_qsl(urlsplit(str(request.url)).query)
                )
                get_all_actions = await model.get_all_actions(request)
                config_model = await model._configs(request)

                return self.templates.TemplateResponse(
                    "edit_quotation.html",
                    {
                        "request": request,
                        "model": model,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj": obj[1],
                        "menu": menu(request),
                    },
                )

            elif obj[0] == "upload_files":
                model11 = self._find_model_from_identity("upload_file")
                get_all_actions = await model11.get_all_actions(request)
                config_model = await model11._configs(request)
                return self.templates.TemplateResponse(
                    "list_upload.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": obj[1],
                        "menu": menu(request),
                    },
                )
            elif obj[0] == "checkinvertory":
                model11 = self._find_model_from_identity("checkinvertory")
                get_all_actions = await model11.get_all_actions(request)
                config_model = await model11._configs(request)
                return self.templates.TemplateResponse(
                    "checkinvertory.html",
                    {
                        "request": request,
                        "model": model,
                        "obj": obj[1],
                        "menu": menu(request),
                    },
                )

        except FormValidationError as exc:
            if model.create_template == "create.html":
                update_error = "Update successful, Update required fields"
            elif model.create_template == "create_invoices.html" and dict_obj["QUERY"]:
                update_error = "Operation not completed yet"
            else:
                update_error = "ERROR, check fields"
            return self.templates.TemplateResponse(
                model.create_template,
                {
                    "request": request,
                    "model": model,
                    "errors": exc.errors,
                    "obj": dict_obj,
                    "update_error": update_error,
                    "menu": menu(request),
                },
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )

        response = self.templates.TemplateResponse(
            model.create_template,
            {
                "request": request,
                "model": model,
                "update": "Successfully Updated",
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

        url = request.url_for(self.route_name + ":list", identity=model.identity)
        if form.get("_continue_editing", None) is not None:
            return RedirectResponse(
                url="/project/items_tbl/create", status_code=HTTP_303_SEE_OTHER
            )

        elif form.get("_add_another", None) is not None:
            return RedirectResponse(
                url="/project/items_tbl/create", status_code=HTTP_303_SEE_OTHER
            )

    async def create_quotation_list(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_create(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        if request.method == "GET":
            return self.templates.TemplateResponse(
                model.create_template,
                {
                    "request": request,
                    "model": model,
                    "menu": menu(request),
                },
            )
        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        try:
            obj = await model.create(request, dict_obj)
        except FormValidationError as exc:
            return self.templates.TemplateResponse(
                model.create_template,
                {
                    "request": request,
                    "model": model,
                    "errors": exc.errors,
                    "obj": dict_obj,
                    "menu": menu(request),
                },
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )
        pk = getattr(obj, model.pk_attr)  # type: ignore
        url = request.url_for(self.route_name + ":list", identity=model.identity)
        if form.get("_continue_editing", None) is not None:
            url = request.url_for(
                self.route_name + ":edit", identity=model.identity, pk=pk
            )
        elif form.get("_add_another", None) is not None:
            url = request.url
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    async def _invoice_create(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_create(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        query_string_list = query_string.split("?")
        query_string_dict = dict(
            (i.split("==")[0], i.split("==")[1]) for i in query_string_list
        )
        dest_db_invoice_create = engine_nick[query_string_dict["choicedb_destination"]]
        Account_Number = query_string_dict["Account_Number"]
        Sales_Rep = query_string_dict["Sales_Rep"]
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d 00:00:00")
        if query_string_dict["invoice"]:
            invoice_number_invoice_create = query_string_dict["invoice"]
        else:
            with Session(engine[dest_db_invoice_create]) as session:
                stmt_quotation_status = select(
                    Customers_tbl.__table__.columns
                ).filter_by(AccountNo=Account_Number)
                answ_quotation_status = (
                    session.execute(stmt_quotation_status).mappings().all()
                )
                stmt_Sales_Rep_status = select(
                    Employees_tbl.__table__.columns
                ).filter_by(FirstName=Sales_Rep)
                answ_Sales_Rep_status = (
                    session.execute(stmt_Sales_Rep_status).mappings().all()
                )
                stmt_InvoiceNumber = select(
                    Invoices_tbl.InvoiceID,
                    Invoices_tbl.InvoiceNumber,
                ).order_by(Invoices_tbl.InvoiceID.desc())
                answ_InvoiceNumber = (
                    session.execute(stmt_InvoiceNumber)
                    .mappings()
                    .all()[0]["InvoiceNumber"]
                )
                new_InvoiceNumber = int(answ_InvoiceNumber) + 1
                stmt_invoice_create = (
                    insert(Invoices_tbl)
                    .values(
                        InvoiceNumber=new_InvoiceNumber,
                        InvoiceDate=time_now_5h,
                        CustomerID=answ_quotation_status[0]["CustomerID"],
                        BusinessName=answ_quotation_status[0]["BusinessName"],
                        AccountNo=answ_quotation_status[0]["AccountNo"],
                        ShipDate=time_now_5h,
                        Shipto=answ_quotation_status[0]["Shipto"],
                        ShipAddress1=answ_quotation_status[0]["Address1"],
                        ShipAddress2=answ_quotation_status[0]["Address2"],
                        ShipContact=answ_quotation_status[0]["ShipContact"],
                        ShipCity=answ_quotation_status[0]["ShipCity"],
                        ShipState=answ_quotation_status[0]["ShipState"],
                        ShipZipCode=answ_quotation_status[0]["ShipZipCode"],
                        ShipPhoneNo=answ_quotation_status[0]["Phone_Number"],
                        TermID=answ_quotation_status[0]["TermID"],
                        SalesRepID=answ_Sales_Rep_status[0]["EmployeeID"],
                    )
                    .returning(
                        Invoices_tbl.InvoiceNumber,
                        Invoices_tbl.InvoiceID,
                    )
                )
            rows_create_invoice = session.execute(stmt_invoice_create).mappings().all()
            InvoiceID_invoice_create = rows_create_invoice[0]["InvoiceID"]
            session.commit()

            invoice_number_invoice_create = new_InvoiceNumber

        query_invoice_dest = f"select * from Invoices_tbl Where InvoiceNumber = {invoice_number_invoice_create}"
        answ_invoice_query = pd_req(query_invoice_dest, dest_db_invoice_create)

        answ_invoice_start_query = pd_req(
            query_string_dict["QUERY"].lower(), query_string_dict["choicedb_source"]
        )
        answ_invoice_lineid_list = [
            i["lineid"] for i in answ_invoice_start_query if "lineid" in i
        ]
        qty_dict = dict((i["lineid"], i["qty"]) for i in answ_invoice_start_query)
        if answ_invoice_query and "InvoiceID" in answ_invoice_query[0]:
            invoice_id = answ_invoice_query[0]["InvoiceID"]
        else:
            exc_invoice = {
                "title": f"InvoicesDetails is not present for this Invoice number {query_string_dict['invoice']} ",
                "detail": "Please make shure that Invoice number is correct",
            }
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "exc": exc_invoice,
                    "menu": menu(request),
                },
                status_code=500,
            )

        if answ_invoice_start_query and answ_invoice_lineid_list:
            ...
        else:
            exc_invoice = {
                "title": f"This invoice {query_string_dict['invoice']} has no InvoicesDetails",
                "detail": "Please make shure that Invoice number is correct",
            }
            return self.templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "exc": exc_invoice,
                    "menu": menu(request),
                },
                status_code=500,
            )

        query_details = f"select * from InvoicesDetails_tbl Where LineID IN ({','.join([str(i) for i in answ_invoice_lineid_list])})"
        answ_query_details = pd_req(query_details, query_string_dict["choicedb_source"])
        bad_items_dict = {}
        with Session(engine[dest_db_invoice_create]) as session:
            for i in answ_query_details:
                try:
                    sku_prod = i["ProductUPC"]
                    query_Items_tbl = f"select * from Items_tbl Where ProductUPC = {mod_value(sku_prod)}"
                    answ_Items_tbl = pd_req(query_Items_tbl, dest_db_invoice_create)

                    query_Packing = f"select UnitDesc from Units_tbl Where UnitID = '{answ_Items_tbl[0]['UnitID']}'"
                    answ_Packing = pd_req(query_Packing, dest_db_invoice_create)
                    if answ_Packing:
                        answ_Packing = answ_Packing[0]["UnitDesc"]
                except IndexError:
                    bad_items_list_temp = list()
                    bad_items_list_temp.append(i["LineID"])
                    bad_items_list_temp.append(i["ProductUPC"])
                    bad_items_list_temp.append(i["ProductDescription"])
                    bad_items_list_temp.append(mod_value(qty_dict[i["LineID"]]))
                    bad_items_dict.update({i["LineID"]: bad_items_list_temp})
                    continue
                if not query_Items_tbl:
                    bad_items_list_temp = list()
                    bad_items_list_temp.append(i["LineID"])
                    bad_items_list_temp.append(i["ProductUPC"])
                    bad_items_list_temp.append(i["ProductDescription"])
                    bad_items_list_temp.append(mod_value(qty_dict[i["LineID"]]))
                    bad_items_dict.update({i["LineID"]: bad_items_list_temp})
                    continue

                if query_string_dict["activated_Invoices_tbl"] == "on":
                    UnitPrice = answ_Items_tbl[0]["UnitPriceC"]
                else:
                    UnitPrice = answ_Items_tbl[0]["UnitPrice"]

                query_new_invoice = f"INSERT INTO [InvoicesDetails_tbl] ([InvoiceID], [CateID], [SubCateID], [UnitDesc], \
                        [UnitQty], [ProductID], [ProductSKU], [ProductUPC], [ProductDescription], [ItemSize], [LineMessage], \
                        [UnitPrice], [OriginalPrice], [RememberPrice], [UnitCost], [Discount], [ds_Percent], [QtyShipped], \
                        [QtyOrdered], [ItemWeight], [Packing], [ExtendedPrice], [ExtendedDisc], [ExtendedCost], [PromotionID], \
                        [PromotionLine], [PromotionDescription], [PromotionAmount], [ActExtendedPrice], [SPPromoted], \
                        [SPPromotionDescription], [Taxable], [ItemTaxID], [Catch], [Negative], [Flag], [Void]) \
                        OUTPUT inserted.[LineID] VALUES ( {invoice_id}, {mod_value(answ_Items_tbl[0]['CateID'])}, \
                        {mod_value(answ_Items_tbl[0]['SubCateID'])}, \
                        {mod_value(i['UnitDesc'])}, {mod_value(i['UnitQty'])}, {mod_value(answ_Items_tbl[0]['ProductID'])}, {mod_value(answ_Items_tbl[0]['ProductSKU'])}, \
                        {mod_value(i['ProductUPC'])}, {mod_value(answ_Items_tbl[0]['ProductDescription'])}, {mod_value(i['ItemSize'])}, {mod_value(i['LineMessage'])}, \
                        {mod_value(UnitPrice)}, {mod_value(i['OriginalPrice'])}, {mod_value(i['RememberPrice'])}, {mod_value(answ_Items_tbl[0]['UnitCost'])}, \
                        {mod_value(i['Discount'])}, {mod_value(i['ds_Percent'])}, {mod_value(qty_dict[i['LineID']])}, {mod_value(qty_dict[i['LineID']])}, {mod_value(answ_Items_tbl[0]['ItemWeight'])}, \
                        {mod_value(answ_Packing)}, {mod_value(qty_dict[i['LineID']]) * mod_value(UnitPrice)}, {mod_value(i['ExtendedDisc'])}, \
                        {mod_value(qty_dict[i['LineID']]) * mod_value(answ_Items_tbl[0]['UnitCost'])}, \
                        {mod_value(i['PromotionID'])}, {mod_value(i['PromotionLine'])}, {mod_value(i['PromotionDescription'])}, {mod_value(i['PromotionAmount'])}, \
                        {mod_value(i['ActExtendedPrice'])}, {mod_value(i['SPPromoted'])}, {mod_value(i['SPPromotionDescription'])}, {mod_value(i['Taxable'])}, \
                        {mod_value(answ_Items_tbl[0]['ItemTaxID'])}, {mod_value(i['Catch'])}, {mod_value(i['Negative'])}, {mod_value(i['Flag'])}, {mod_value(i['Void'])})"

                query_new_invoice = " ".join(query_new_invoice.split())

                answ = session.execute(text(query_new_invoice))
            session.commit()

            stmt_checkdet_invoice_create = select(
                func.sum(InvoicesDetails_tbl.QtyShipped).label("TotQtyOrd"),
                func.sum(
                    InvoicesDetails_tbl.UnitPrice * InvoicesDetails_tbl.QtyShipped
                ).label("InvoiceSubtotal"),
                func.count(InvoicesDetails_tbl.LineID).label("NoLines"),
            ).where(InvoicesDetails_tbl.InvoiceID == invoice_id)

            answ_checkdet_invoice_create = (
                session.execute(stmt_checkdet_invoice_create).mappings().all()
            )
            stmt_update_new_invoice = (
                update(Invoices_tbl)
                .values(
                    TotQtyOrd=answ_checkdet_invoice_create[0]["TotQtyOrd"],
                    TotQtyShp=answ_checkdet_invoice_create[0]["TotQtyOrd"],
                    NoLines=answ_checkdet_invoice_create[0]["NoLines"],
                    InvoiceSubtotal=answ_checkdet_invoice_create[0]["InvoiceSubtotal"],
                    InvoiceTotal=answ_checkdet_invoice_create[0]["InvoiceSubtotal"],
                )
                .where(Invoices_tbl.InvoiceNumber == invoice_number_invoice_create)
            )

            answ_update_new_invoice = session.execute(stmt_update_new_invoice)
            session.commit()
        bad_items_list = list()
        bad_items_list.append("ERROR Operation not completed")
        for i in bad_items_dict:
            bad_items_dict_text = f"- ID: {bad_items_dict[i][0]}, UPC: {bad_items_dict[i][1]}, DESCR: {bad_items_dict[i][2]}, QTY: {bad_items_dict[i][3]}"
            bad_items_list.append(bad_items_dict_text)
        try:
            if bad_items_dict:
                raise FormValidationError(bad_items_dict)
        except FormValidationError as exc:

            response = self.templates.TemplateResponse(
                model.create_template,
                {
                    "request": request,
                    "model": model,
                    "errors": exc.errors,
                    "obj": {},
                    "update_error_list": bad_items_list,
                    "menu": menu(request),
                },
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

        response = self.templates.TemplateResponse(
            model.create_template,
            {
                "request": request,
                "model": model,
                "obj": {},
                "update": "Successfully Updated",
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def queryalias1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "queryalias1"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            response = JSONResponse(res_dict)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

        items = await model.find_all_queryalias1(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        total = await model.count(request=request, where=where)
        if len(items) == 1:
            flag = 0
        else:
            flag = 1
        for item in items:
            res_dict_temp = {}
            alias = f"{item[0]}"
            query_alias = f"{item[1]}"
            res_dict_temp.update(
                {
                    "id": alias,
                    "queryalias1": query_alias,
                    "_select2_selection": f"<span><strong>{alias}</strong></span>",
                    "_select2_result": f"<span><strong>{alias}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)

        response = JSONResponse(res_dict)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def accountnumbercopy(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "accountnumbercopy"
        model = self._find_model_from_identity("invoices_tbl")
        query_view_accountnumbercopy = dict(parse_qsl(urlsplit(str(request.url)).query))
        form = await request.form()
        list_obj_detail: list[str] = list()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            response = JSONResponse(res_dict)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        source_db_form = ""
        if "dop" in query_view_accountnumbercopy:
            query_string_dict_dop = query_view_accountnumbercopy["dop"]
            source_db_form = query_view_accountnumbercopy["dop"]
        else:
            response = JSONResponse(res_dict)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        if query_view_accountnumbercopy["dop"] != None:
            items = await model.find_all_accountnumbercopy(
                request=request,
                skip=skip,
                limit=limit,
                where=where,
                order_by=order_by,
                other=identity1,
                dict_obj=dict_obj,
                model=model,
                db_form=source_db_form,
            )
            if len(items) == 1:
                flag = 0
            else:
                flag = 1

            for item in items:
                res_dict_temp = {}
                alias = f"{item['CustomerID']}"
                query_alias = f"{item['AccountNo']}"
                query_alias_dop = f"{item['BusinessName']}"
                res_dict_temp.update(
                    {
                        "id": query_alias,
                        "accountnumbercopy": query_alias,
                        "_select2_selection": f"<span><strong>{query_alias} - {query_alias_dop}</strong></span>",
                        "_select2_result": f"<span><strong>{query_alias} - {query_alias_dop}</strong></span>",
                        "flag": flag,
                    }
                )
                res_dict["items"].append(res_dict_temp)
            response = JSONResponse(res_dict)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def salesrepinvoices(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "salesrepinvoices"
        model = self._find_model_from_identity("invoices_tbl")
        query_view_salesrepinvoices = dict(parse_qsl(urlsplit(str(request.url)).query))
        form = await request.form()
        list_obj_detail: list[str] = list()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            response = JSONResponse(res_dict)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        source_db_form = ""
        if "dop" in query_view_salesrepinvoices:
            query_string_dict_dop = query_view_salesrepinvoices["dop"]
            source_db_form = query_view_salesrepinvoices["dop"]
        else:
            response = JSONResponse(res_dict)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        if query_view_salesrepinvoices["dop"] != None:
            items = await model.find_all_salesrepinvoices(
                request=request,
                skip=skip,
                limit=limit,
                where=where,
                order_by=order_by,
                other=identity1,
                dict_obj=dict_obj,
                model=model,
                db_form=source_db_form,
            )

            if len(items) == 1:
                flag = 0
            else:
                flag = 1

            for item in items:
                res_dict_temp = {}
                alias = f"{item['EmployeeID']}"
                query_alias = f"{item['FirstName']}"
                res_dict_temp.update(
                    {
                        "id": query_alias,
                        "salesrepinvoices": query_alias,
                        "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                        "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                        "flag": flag,
                    }
                )
                res_dict["items"].append(res_dict_temp)
            response = JSONResponse(res_dict)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def choicedbdestination(self, request: Request) -> Response:
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        res_dict = {"items": []}
        query_string_dict = dict(parse_qsl(query_string))
        source_db_form = ""
        identity1 = "choicedbdestination"
        model = self._find_model_from_identity("invoices_tbl")
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        items = await model.find_all_choicedbdestination(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
            dict_obj=dict_obj,
            model=model,
            db_form=source_db_form,
        )
        if len(items) == 1:
            flag = 0
        elif len(items) > 1:
            if items[0]["Nick"] == items[1]["Nick"]:
                flag = 0
            else:
                flag = 1
        for item in items:
            res_dict_temp = {}
            alias = f'{item["NameDB"]}'
            query_alias = f'{item["Nick"]}'
            res_dict_temp.update(
                {
                    "id": query_alias,
                    "choicedbdestination": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                    "item_id": item["id"],
                }
            )
            res_dict["items"].append(res_dict_temp)
        response = JSONResponse(res_dict)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def choicedbdestination1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "choicedbdestination1"
        model = self._find_model_from_identity("invoices_tbl")
        query_view_edit_quotation = dict(parse_qsl(urlsplit(str(request.url)).query))
        form = await request.form()
        list_obj_detail: list[str] = list()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            response = JSONResponse(res_dict)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        response = self.templates.TemplateResponse(
            "create_new_quotation.html",
            {
                "request": request,
                "model": model,
                "obj": dict_obj,
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

        items = [(i["Nick"], i["NameDB"]) for i in rows_quotation_db]

        print(items, "itemseeeeeeeeee_choicedbdestination1nnnn")

        for item in items:
            print(item, "----choicedbdestination1")
            res_dict_temp = {}
            alias = f"{item[0]}"
            query_alias = f"{item[1]}"
            res_dict_temp.update(
                {
                    "id": alias,
                    "choicedbdestination1": query_alias,
                    "_select2_selection": f"<span><strong>{alias}</strong></span>",
                    "_select2_result": f"<span><strong>{alias}</strong></span>",
                }
            )
            res_dict["items"].append(res_dict_temp)

        return JSONResponse(res_dict)

    async def new_quotation_edit(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "new_quotation_edit"
        model = self._find_model_from_identity(identity)
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)

        query_new_quotation_edit = dict(parse_qsl(urlsplit(str(request.url)).query))
        model = self._find_model_from_identity("quotations1_tbl")
        get_all_actions = await model.get_all_actions(request)
        config_model = await model._configs(request)
        return self.templates.TemplateResponse(
            "create_new_quotation.html",
            {
                "request": request,
                "model": model,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "obj": query_new_quotation_edit,
                "url": "http://192.168.1.140/project/quotations1_tbl/list",
                "menu": menu(request),
            },
        )

    async def new_quotation_delete(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "new_quotation_delete"
        model = self._find_model_from_identity(identity)
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        query_new_quotation_delete = dict(parse_qsl(urlsplit(str(request.url)).query))
        with Session(engine["DB_admin"]) as session:
            stmt_delete = delete(QuotationsTemp).where(
                QuotationsTemp.id == query_new_quotation_delete["id"]
            )
            answ_delete = session.execute(stmt_delete)
            session.commit()
        return RedirectResponse(
            url="/project/quotations1_tbl/list", status_code=HTTP_303_SEE_OTHER
        )

    async def new_quotation_edit_delete(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "new_quotation_edit_delete"
        model = self._find_model_from_identity(identity)
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        query_new_quotation_edit_delete = dict(
            parse_qsl(urlsplit(str(request.url)).query)
        )
        source_db = query_new_quotation_edit_delete["SourceDB"]
        LineID = query_new_quotation_edit_delete["LineID"]
        QuotationID = query_new_quotation_edit_delete["QuotationID"]
        with Session(engine[engine_nick[source_db]]) as session:
            stmt_QuotationID = select(Quotations_tbl.__table__.columns).filter_by(
                QuotationID=QuotationID
            )
            rows_QuotationID = session.execute(stmt_QuotationID).mappings().all()
            QuotationNumber = rows_QuotationID[0]["QuotationNumber"]
            stmt_delete = delete(QuotationsDetails_tbl).where(
                QuotationsDetails_tbl.LineID == LineID
            )
            answ_delete = session.execute(stmt_delete)
            session.commit()
            stmt_quotation_delete_sum = select(
                QuotationsDetails_tbl.UnitPrice,
                QuotationsDetails_tbl.Qty,
            ).where(
                QuotationsDetails_tbl.QuotationID == QuotationID,
            )
            rows_quotation_delete_sum = (
                session.execute(stmt_quotation_delete_sum).mappings().all()
            )
            total_sum: list[str] = list()
            for i in rows_quotation_delete_sum:
                total_sum.append(float(i["UnitPrice"]) * float(i["Qty"]))
            stmt_delete_quotation_sum = (
                update(Quotations_tbl)
                .values(
                    QuotationTotal=sum(total_sum),
                )
                .where(Quotations_tbl.QuotationID == QuotationID)
            )
            answ_update_quotation_details = session.execute(stmt_delete_quotation_sum)
            session.commit()

        return RedirectResponse(
            url=f"/project/quotations3_tbl/list?DBname={source_db}&QuotationID={QuotationID}&QuotationNumber={QuotationNumber}&status=view_details",
            status_code=HTTP_303_SEE_OTHER,
        )
    
    async def view_invoice(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)

        invoice_query = dict(
            parse_qsl(urlsplit(str(request.url)).query)
        )
        invoiceID = invoice_query["InvoiceID"]
        invoiceDB = invoice_query["DBname"]
        
        with Session(engine[engine_nick[invoiceDB]]) as session:
            stmt = select(InvoicesDetails_tbl.__table__.columns).filter_by(
                InvoiceID=invoiceID
            )
            rows = session.execute(stmt).mappings().all()
            rows_serializable = [dict(row) for row in rows]
        return JSONResponse(content=rows_serializable)
        

    async def quotation_update(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "quotation_update"
        model = self._find_model_from_identity(identity)
        get_all_actions = await model.get_all_actions(request)
        config_model = await model._configs(request)
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        quotation_number_0 = dict(parse_qsl(urlsplit(str(request.url)).query))
        quotation_number = quotation_number_0["QuotationNumber"]
        invoice_number = quotation_number_0["InvoiceNumber"]
        update_success = f"Invoice: {invoice_number} Successfully Update"
        with Session(engine["DB_admin"]) as session:
            stmt_quotation_status = select(Quotation.__table__.columns).filter_by(
                InvoiceNumber=invoice_number
            )
            rows_quotation_status = (
                session.execute(stmt_quotation_status).mappings().all()
            )
            if rows_quotation_status and rows_quotation_status[0]["Status"] == "VOIDED":
                response = self.templates.TemplateResponse(
                    "create_quotation.html",
                    {
                        "request": request,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "model": self._find_model_from_identity("quotations_tbl"),
                        "update_error": f"Invoice: {invoice_number} canceled and cannot be updated",
                        "menu": menu(request),
                    },
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            stmt_quotation_update = select(QuotationDetails.__table__.columns).where(
                QuotationDetails.InvoiceNumber == invoice_number
            )
            rows_quotation_update_temp = session.execute(stmt_quotation_update).all()
            rows_quotation_update = [
                row._asdict() for row in rows_quotation_update_temp
            ]
        source_db = rows_quotation_status[0]["SourceDB"]
        rows_quotation_update_dict_admin = dict()
        for i in rows_quotation_update:
            if i["ProductUPC"] in rows_quotation_update_dict_admin:
                ProductUPC = i["ProductUPC"]
                quant_admin_start = rows_quotation_update_dict_admin[ProductUPC]["QTY"]
                quant_admin_end = i["QTY"]
                rows_quotation_update_dict_admin[ProductUPC].update(
                    {"QTY": quant_admin_start + quant_admin_end}
                )
                continue
            else:
                rows_quotation_update_dict_admin[i["ProductUPC"]] = i
        with Session(engine[engine_nick[source_db]]) as session:
            answ_AutoOrderNo = invoice_number
            if answ_AutoOrderNo and answ_AutoOrderNo != None:
                stmt_autoorder = (
                    select(InvoicesDetails_tbl.__table__.columns)
                    .join(
                        Invoices_tbl,
                        InvoicesDetails_tbl.InvoiceID == Invoices_tbl.InvoiceID,
                    )
                    .where(Invoices_tbl.InvoiceNumber == answ_AutoOrderNo)
                )
                answ_autoorder = session.execute(stmt_autoorder).mappings().all()
                answ_autoorder_dict_baza = dict(
                    (i["ProductUPC"], i["QtyShipped"])
                    for i in answ_autoorder
                    if i["ProductUPC"] != None
                )
                answ_quotationdetails_dict_baza = dict()
                for i in answ_autoorder:
                    if i["ProductUPC"] != None:
                        answ_quotationdetails_dict_baza[i["ProductUPC"]] = dict(i)
                        answ_quotationdetails_dict_baza[i["ProductUPC"]].update(
                            {"Qty": i["QtyShipped"]}
                        )
                with Session(engine["DB_admin"]) as session2:
                    stmt_autoorder_update = (
                        update(Quotation)
                        .values(InvoiceNumber=answ_AutoOrderNo, FlagOrder=True)
                        .where(Quotation.QuotationNumber == quotation_number)
                    )
                    rows_autoorder_update = session2.execute(stmt_autoorder_update)
                    session2.commit()
        answ_quotationdetails_dict_baza1 = copy.deepcopy(
            answ_quotationdetails_dict_baza
        )
        check_dublicate = list()
        quotationdetails_dest_error_list = []
        with Session(engine["DB1"]) as session:
            with Session(engine["DB_admin"]) as session1:
                answ_quotationdetails_dict_baza2 = copy.deepcopy(
                    answ_quotationdetails_dict_baza
                )
                for i in answ_quotationdetails_dict_baza2:

                    stmt_Items_tbl = select(
                        Items_tbl.__table__.columns.QuantOnHand
                    ).where(
                        Items_tbl.ProductUPC
                        == answ_quotationdetails_dict_baza1[i]["ProductUPC"]
                    )
                    answ_Items_tbl = session.execute(stmt_Items_tbl).mappings().all()
                    if not answ_Items_tbl:
                        ProductDescription = answ_quotationdetails_dict_baza2[i][
                            "ProductDescription"
                        ]
                        ProductUPC = answ_quotationdetails_dict_baza2[i]["ProductUPC"]
                        Qty = answ_quotationdetails_dict_baza2[i]["Qty"]
                        quotationdetails_dest_error_list.append(
                            f"Not Updated -- Description: {ProductDescription} UPC: {ProductUPC} Quantity: {Qty}"
                        )
                        answ_quotationdetails_dict_baza.pop(i)
                        continue
                for i in answ_quotationdetails_dict_baza:
                    stmt_Items_tbl = select(
                        Items_tbl.__table__.columns.QuantOnHand
                    ).where(
                        Items_tbl.ProductUPC
                        == answ_quotationdetails_dict_baza[i]["ProductUPC"]
                    )
                    answ_Items_tbl = session.execute(stmt_Items_tbl).mappings().all()
                    if not answ_Items_tbl:
                        continue
                    if i in rows_quotation_update_dict_admin:
                        quant_admin = rows_quotation_update_dict_admin[i]["QTY"] * -1
                        quant_baza = answ_quotationdetails_dict_baza[i]["Qty"]
                        if quant_admin == quant_baza:
                            continue
                        elif quant_admin > quant_baza:
                            quant_final = quant_admin - quant_baza
                        elif quant_admin < quant_baza:
                            quant_final = (quant_baza - quant_admin) * -1
                    else:
                        quant_final = answ_quotationdetails_dict_baza[i]["Qty"] * -1
                    if answ_AutoOrderNo and answ_AutoOrderNo != None:
                        stmt = insert(QuotationDetails).values(
                            QuotationNumber=quotation_number,
                            ProductDescription=answ_quotationdetails_dict_baza[i][
                                "ProductDescription"
                            ],
                            ProductSKU=answ_quotationdetails_dict_baza[i]["ProductSKU"],
                            ProductUPC=answ_quotationdetails_dict_baza[i]["ProductUPC"],
                            QTY=quant_final,
                            InvoiceNumber=answ_AutoOrderNo,
                            FlagOrder=True,
                        )
                    else:
                        stmt = insert(QuotationDetails).values(
                            QuotationNumber=quotation_number,
                            ProductDescription=answ_quotationdetails_dict_baza[i][
                                "ProductDescription"
                            ],
                            ProductSKU=answ_quotationdetails_dict_baza[i]["ProductSKU"],
                            ProductUPC=answ_quotationdetails_dict_baza[i]["ProductUPC"],
                            QTY=quant_final,
                            FlagOrder=False,
                        )
                    rows = session1.execute(stmt).mappings().all()
                    answ_Items_tbl = answ_Items_tbl[0]["QuantOnHand"]
                    qty_items = answ_Items_tbl + quant_final
                    stmt_update_items = (
                        update(Items_tbl)
                        .values(QuantOnHand=qty_items)
                        .where(
                            Items_tbl.ProductUPC
                            == answ_quotationdetails_dict_baza[i]["ProductUPC"]
                        )
                    )
                    answ_update_items = session.execute(stmt_update_items)
                stmt_quotation_update = (
                    update(Quotation)
                    .values(
                        Status="UPDATED",
                        LastUpdate=time_now_5h,
                    )
                    .where(Quotation.InvoiceNumber == invoice_number)
                )
                rows_quotation_update = session1.execute(stmt_quotation_update)
                session1.commit()
                if answ_quotationdetails_dict_baza:
                    for i in rows_quotation_update_dict_admin:
                        stmt_Items_tbl1 = select(
                            Items_tbl.__table__.columns.QuantOnHand
                        ).where(
                            Items_tbl.ProductUPC
                            == rows_quotation_update_dict_admin[i]["ProductUPC"]
                        )
                        answ_Items_tbl1 = (
                            session.execute(stmt_Items_tbl1).mappings().all()
                        )

                        if i in answ_quotationdetails_dict_baza:
                            continue
                        else:
                            quant_final = (
                                rows_quotation_update_dict_admin[i]["QTY"] * -1
                            )

                            if quant_final != 0:
                                if answ_AutoOrderNo and answ_AutoOrderNo != None:
                                    stmt = insert(QuotationDetails).values(
                                        QuotationNumber=quotation_number,
                                        ProductDescription=rows_quotation_update_dict_admin[
                                            i
                                        ][
                                            "ProductDescription"
                                        ],
                                        ProductSKU=rows_quotation_update_dict_admin[i][
                                            "ProductSKU"
                                        ],
                                        ProductUPC=rows_quotation_update_dict_admin[i][
                                            "ProductUPC"
                                        ],
                                        QTY=quant_final,
                                        InvoiceNumber=answ_AutoOrderNo,
                                        FlagOrder=True,
                                    )

                                else:
                                    stmt = insert(QuotationDetails).values(
                                        QuotationNumber=quotation_number,
                                        ProductDescription=rows_quotation_update_dict_admin[
                                            i
                                        ][
                                            "ProductDescription"
                                        ],
                                        ProductSKU=rows_quotation_update_dict_admin[i][
                                            "ProductSKU"
                                        ],
                                        ProductUPC=rows_quotation_update_dict_admin[i][
                                            "ProductUPC"
                                        ],
                                        QTY=quant_final,
                                        FlagOrder=False,
                                    )
                                rows = session1.execute(stmt).mappings().all()
                                answ_Items_tbl1 = answ_Items_tbl1[0]["QuantOnHand"]
                                qty_items1 = answ_Items_tbl1 + quant_final
                                stmt_update_items = (
                                    update(Items_tbl)
                                    .values(QuantOnHand=qty_items1)
                                    .where(Items_tbl.ProductUPC == i)
                                )
                                answ_update_items = session.execute(stmt_update_items)
                session1.commit()
                session.commit()
        response = self.templates.TemplateResponse(
            "create_quotation.html",
            {
                "request": request,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "model": self._find_model_from_identity("quotations_tbl"),
                "update": update_success,
                "update_error_list": quotationdetails_dest_error_list,
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def list_quotation(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "list_quotation"
        model = self._find_model_from_identity(identity)
        time_now = datetime.datetime.today().strftime("%Y-%m-%d 00:00:00")
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        query_list_quotation = dict(parse_qsl(urlsplit(str(request.url)).query))
        model11 = self._find_model_from_identity("quotations2_tbl")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        quotationdetails_dest_dict: Dict[int, int] = {}
        quotationdetails_dest_error_dict: Dict[int, int] = {}
        quotationdetails_dest_error_list = []
        successfully = ""
        answ_quotation_items_dict = {}
        with Session(engine[engine_nick[query_list_quotation["DBname"]]]) as session:
            stmt_InvoiceNumber = select(Invoices_tbl.__table__.columns).order_by(
                Invoices_tbl.InvoiceID.desc()
            )
            answ_InvoiceNumber = (
                session.execute(stmt_InvoiceNumber).mappings().all()[0]["InvoiceNumber"]
            )
            new_InvoiceNumber = int(answ_InvoiceNumber) + 1
            query_quotation = select(Quotations_tbl.__table__.columns).filter_by(
                QuotationID=query_list_quotation["QuotationID"]
            )
            answ_quotation_number = session.execute(query_quotation).mappings().all()
            query_QuotationsDetails = select(
                QuotationsDetails_tbl.__table__.columns
            ).filter_by(QuotationID=query_list_quotation["QuotationID"])
            answ_QuotationsDetails = (
                session.execute(query_QuotationsDetails).mappings().all()
            )
            query_QuotationsDetails_qty = select(
                func.sum(QuotationsDetails_tbl.Qty).label("QuotationsDetails_qty")
            ).filter_by(QuotationID=query_list_quotation["QuotationID"])
            answer_QuotationsDetails_qty = (
                session.execute(query_QuotationsDetails_qty)
                .mappings()
                .all()[0]["QuotationsDetails_qty"]
            )
            query_employees = (
                select(Employees_tbl.FirstName)
                .join(
                    Quotations_tbl,
                    Employees_tbl.EmployeeID == Quotations_tbl.SalesRepID,
                )
                .where(
                    Quotations_tbl.QuotationNumber
                    == query_list_quotation["QuotationNumber"]
                )
            )
            answer_employees = (
                session.execute(query_employees)
                .mappings()
                .all()[0]["FirstName"]
                .strip()
                .lower()
            )
            quotationdetails_dict = dict(
                (i["ProductUPC"], i["Qty"]) for i in answ_QuotationsDetails
            )
            quotationdetails_all_dict = dict(
                (i["ProductUPC"], i) for i in answ_QuotationsDetails
            )
            quotationdetails_descr_dict = dict(
                (i["ProductUPC"], i["ProductDescription"])
                for i in answ_QuotationsDetails
            )
            quotation_dict = dict((i["QuotationID"], i) for i in answ_quotation_number)
            with Session(engine["DB1"]) as session1:
                for i1 in quotationdetails_dict:
                    query_quotation_items = select(Items_tbl.QuantOnHand).filter_by(
                        ProductUPC=i1
                    )
                    answ_quotation_items = (
                        session1.execute(query_quotation_items).mappings().all()
                    )
                    if answ_quotation_items:
                        for i2 in range(len(answ_quotation_items)):
                            quotationdetails_dest_dict[i1] = (
                                answ_quotation_items[i2]["QuantOnHand"]
                                - quotationdetails_dict[i1]
                            )

                    else:
                        quotationdetails_dest_error_list.append(
                            f"In invoice {new_InvoiceNumber} not added: Description - {quotationdetails_descr_dict[i1]} UPC - {i1}"
                        )
            if not quotationdetails_dest_error_list:
                successfully = f"Successfully create Invoice {new_InvoiceNumber}"
            stmt = (
                insert(Invoices_tbl)
                .values(
                    InvoiceNumber=new_InvoiceNumber,
                    InvoiceDate=time_now,
                    InvoiceTitle=answ_quotation_number[0]["QuotationTitle"],
                    CustomerID=answ_quotation_number[0]["CustomerID"],
                    BusinessName=answ_quotation_number[0]["BusinessName"],
                    AccountNo=answ_quotation_number[0]["AccountNo"],
                    PoNumber=answ_quotation_number[0]["PoNumber"],
                    ShipDate=time_now,
                    Shipto=answ_quotation_number[0]["Shipto"],
                    ShipAddress1=answ_quotation_number[0]["ShipAddress1"],
                    ShipAddress2=answ_quotation_number[0]["ShipAddress2"],
                    ShipContact=answ_quotation_number[0]["ShipContact"],
                    ShipCity=answ_quotation_number[0]["ShipCity"],
                    ShipState=answ_quotation_number[0]["ShipState"],
                    ShipZipCode=answ_quotation_number[0]["ShipZipCode"],
                    ShipPhoneNo=answ_quotation_number[0]["ShipPhoneNo"],
                    TermID=answ_quotation_number[0]["TermID"],
                    SalesRepID=answ_quotation_number[0]["SalesRepID"],
                    ShipperID=answ_quotation_number[0]["ShipperID"],
                    TotQtyOrd=answer_QuotationsDetails_qty,
                    TotQtyShp=answer_QuotationsDetails_qty,
                    NoLines=len(answ_QuotationsDetails),
                    InvoiceSubtotal=answ_quotation_number[0]["QuotationTotal"],
                    TotalTaxes=answ_quotation_number[0]["TotalTaxes"],
                    InvoiceTotal=answ_quotation_number[0]["QuotationTotal"],
                    Notes=answ_quotation_number[0]["Notes"],
                    Header=answ_quotation_number[0]["Header"],
                    Footer=answ_quotation_number[0]["Footer"],
                )
                .returning(
                    Invoices_tbl.__table__.columns,
                )
            )
            rows_create_invoice = session.execute(stmt).mappings().all()
            new_invoice_id = rows_create_invoice[0]["InvoiceID"]
            stmt_update_Quotations = (
                update(Quotations_tbl)
                .values(AutoOrderNo=new_InvoiceNumber)
                .filter_by(QuotationID=query_list_quotation["QuotationID"])
            )
            rows_update_Quotations = session.execute(stmt_update_Quotations)
            for i in answ_QuotationsDetails:
                stmt_create_InvoicesDetails = (
                    insert(InvoicesDetails_tbl)
                    .values(
                        InvoiceID=new_invoice_id,
                        CateID=i["CateID"],
                        SubCateID=i["SubCateID"],
                        UnitDesc=i["UnitDesc"],
                        UnitQty=i["UnitQty"],
                        ProductID=i["ProductID"],
                        ProductSKU=i["ProductSKU"],
                        ProductUPC=i["ProductUPC"],
                        ProductDescription=i["ProductDescription"],
                        ItemSize=i["ItemSize"],
                        LineMessage=i["LineMessage"],
                        UnitPrice=i["UnitPrice"],
                        OriginalPrice=i["OriginalPrice"],
                        RememberPrice=i["RememberPrice"],
                        UnitCost=i["UnitCost"],
                        Discount=i["Discount"],
                        ds_Percent=i["ds_Percent"],
                        QtyShipped=i["Qty"],
                        QtyOrdered=i["Qty"],
                        ItemWeight=i["ItemWeight"],
                        ExtendedPrice=i["ExtendedPrice"],
                        ExtendedDisc=i["ExtendedDisc"],
                        ExtendedCost=i["ExtendedCost"],
                        PromotionID=i["PromotionID"],
                        PromotionLine=i["PromotionLine"],
                        PromotionDescription=i["PromotionDescription"],
                        PromotionAmount=i["PromotionAmount"],
                        ActExtendedPrice=i["ActExtendedPrice"],
                        SPPromoted=i["SPPromoted"],
                        SPPromotionDescription=i["SPPromotionDescription"],
                        Taxable=i["Taxable"],
                        ItemTaxID=i["ItemTaxID"],
                        Catch=i["Catch"],
                        Flag=i["Flag"],
                    )
                    .returning(
                        InvoicesDetails_tbl.LineID,
                    )
                )
                rows_create_InvoicesDetails = (
                    session.execute(stmt_create_InvoicesDetails).mappings().all()
                )
            session.commit()

        with Session(engine["DB1"]) as session:
            for i in quotationdetails_dest_dict:
                if quotationdetails_dest_dict[i] < 0:
                    quotationdetails_dest_error_list.append(
                        f"Оut of stock -- Description: {quotationdetails_descr_dict[i]} UPC: {i} Quantity: {quotationdetails_dest_dict[i]}"
                    )
                query_insert_quotation_Items_tbl = (
                    update(Items_tbl)
                    .values(QuantOnHand=quotationdetails_dest_dict[i])
                    .filter_by(ProductUPC=i)
                )
                rows_insert_quotation_Items_tbl = session.execute(
                    query_insert_quotation_Items_tbl
                )
            session.commit()
        with Session(engine["DB_admin"]) as session:
            stmt_delete = delete(QuotationDetails).where(
                and_(
                    QuotationDetails.QuotationNumber
                    == query_list_quotation["QuotationNumber"],
                    QuotationDetails.InvoiceNumber == None,
                )
            )
            answ_delete = session.execute(stmt_delete)
            session.commit()
        with Session(engine["DB_admin"]) as session:
            BusinessName = answ_quotation_number[0]["BusinessName"]
            SalesRepresentative = answer_employees
            time_now = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            query_check_Quotation_admin = select(Quotation.__table__.columns).filter_by(
                QuotationNumber=query_list_quotation["QuotationNumber"]
            )
            rows_check_Quotation_admin = (
                session.execute(query_check_Quotation_admin).mappings().all()
            )
            if rows_check_Quotation_admin:
                stmt_Quotation_admin = (
                    update(Quotation)
                    .values(
                        InvoiceNumber=new_InvoiceNumber,
                        LastUpdate=time_now_5h,
                        FlagOrder=True,
                    )
                    .filter_by(QuotationNumber=query_list_quotation["QuotationNumber"])
                )
                rows_Quotation_admin = session.execute(stmt_Quotation_admin)
            else:
                stmt_Quotation_admin = (
                    insert(Quotation)
                    .values(
                        QuotationNumber=query_list_quotation["QuotationNumber"],
                        SalesRepresentative=SalesRepresentative.replace("'", "''"),
                        BusinessName=BusinessName.replace("'", "''"),
                        Status="RESERVED",
                        DateCreate=time_now_5h,
                        LastUpdate=time_now_5h,
                        SourceDB=query_list_quotation["DBname"],
                        InvoiceNumber=new_InvoiceNumber,
                        FlagOrder=True,
                    )
                    .returning(
                        Quotation.id,
                    )
                )
                rows_Quotation_admin = (
                    session.execute(stmt_Quotation_admin).mappings().all()
                )
            for i in quotationdetails_dest_dict:
                ProductDescription = quotationdetails_descr_dict[i]
                QTY = quotationdetails_dict[i]
                ProductSKU = quotationdetails_all_dict[i]["ProductSKU"]
                ProductUPC = quotationdetails_all_dict[i]["ProductUPC"]
                stmt_QuotationDetails_admin = (
                    insert(QuotationDetails)
                    .values(
                        QuotationNumber=query_list_quotation["QuotationNumber"],
                        ProductDescription=ProductDescription,
                        ProductSKU=ProductSKU,
                        ProductUPC=ProductUPC,
                        QTY=QTY * -1,
                        InvoiceNumber=new_InvoiceNumber,
                        FlagOrder=True,
                    )
                    .returning(
                        QuotationDetails.id,
                    )
                )
                rows_QuotationDetails_admin = (
                    session.execute(stmt_QuotationDetails_admin).mappings().all()
                )
            session.commit()
        response = self.templates.TemplateResponse(
            "list_all_quotation.html",
            {
                "request": request,
                "model": model,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "update_error_list": quotationdetails_dest_error_list,
                "update": successfully,
                "obj": {},
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def delete_quotation(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "list_quotation"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)

        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        query_delete_quotation = dict(parse_qsl(urlsplit(str(request.url)).query))
        model11 = self._find_model_from_identity("quotations2_tbl")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        quotationdetails_dest_dict: Dict[int, int] = {}
        quotationdetails_dest_error_dict: Dict[int, int] = {}
        quotationdetails_dest_error_list = []
        successfully = ""
        answ_quotation_items_dict = {}
        QuotationID = query_delete_quotation["QuotationID"]
        DBname = query_delete_quotation["DBname"]
        QuotationNumber = query_delete_quotation["QuotationNumber"]
        with Session(engine[engine_nick[DBname]]) as session:
            query_quotation = select(Quotations_tbl.__table__.columns).filter_by(
                QuotationID=QuotationID
            )
            answ_quotation = session.execute(query_quotation).mappings().all()
            stmt_delete = delete(Quotations_tbl).where(
                Quotations_tbl.QuotationID == QuotationID
            )
            answ_delete = session.execute(stmt_delete)
            stmt_delete = delete(QuotationsDetails_tbl).where(
                QuotationsDetails_tbl.QuotationID == QuotationID
            )
            answ_delete = session.execute(stmt_delete)
            session.commit()
        with Session(engine["DB_admin"]) as session:
            stmt_quotation_update = (
                update(Quotation)
                .values(
                    QuotationNumber=None,
                )
                .where(Quotation.QuotationNumber == QuotationNumber)
            )
            rows_quotation_update = session.execute(stmt_quotation_update)
            session.commit()
            response = self.templates.TemplateResponse(
                "list_all_quotation.html",
                {
                    "request": request,
                    "model": model,
                    "_actions": get_all_actions,
                    "__js_model__": config_model,
                    "obj": {},
                    "menu": menu(request),
                },
            )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def delete_quotation_details(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "list_quotation"
        dict_obj: dict[str:str] = dict()
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        query_delete_quotation_details = dict(
            parse_qsl(urlsplit(str(request.url)).query)
        )
        model11 = self._find_model_from_identity("quotationsdetails1_tbl")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        quotationdetails_dest_dict: Dict[int, int] = {}
        quotationdetails_dest_error_dict: Dict[int, int] = {}
        quotationdetails_dest_error_list = []
        successfully = ""
        answ_quotation_items_dict = {}
        LineID = query_delete_quotation_details["LineID"]
        DBname = query_delete_quotation_details["DBname"]
        ProductDescription = query_delete_quotation_details["ProductDescription"]
        QuotationID = query_delete_quotation_details["QuotationID"]
        with Session(engine[engine_nick[DBname]]) as session:
            stmt_delete = delete(QuotationsDetails_tbl).where(
                QuotationsDetails_tbl.LineID == LineID
            )
            answ_delete = session.execute(stmt_delete)
            session.commit()
            stmt_quotation_delete_sum = select(
                QuotationsDetails_tbl.UnitPrice,
                QuotationsDetails_tbl.Qty,
            ).where(
                QuotationsDetails_tbl.QuotationID == QuotationID,
            )
            rows_quotation_delete_sum = (
                session.execute(stmt_quotation_delete_sum).mappings().all()
            )
            total_sum: list[str] = list()
            for i in rows_quotation_delete_sum:
                total_sum.append(float(i["UnitPrice"]) * float(i["Qty"]))
            stmt_delete_quotation_sum = (
                update(Quotations_tbl)
                .values(
                    QuotationTotal=sum(total_sum),
                )
                .where(Quotations_tbl.QuotationID == QuotationID)
            )
            answ_update_quotation_details = session.execute(stmt_delete_quotation_sum)
            session.commit()
            stmt_quotation_delete = (
                select(
                    Quotations_tbl.__table__.columns,
                    QuotationsDetails_tbl.LineID.label("QuotationsDetails_id"),
                    QuotationsDetails_tbl.ProductDescription.label(
                        "QuotationsDetails_ProductDescription"
                    ),
                    QuotationsDetails_tbl.ProductSKU.label(
                        "QuotationsDetails_ProductSKU"
                    ),
                )
                .join(
                    QuotationsDetails_tbl,
                    Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                )
                .where(
                    QuotationsDetails_tbl.QuotationID == QuotationID,
                )
            )
            rows_quotation_edit = (
                session.execute(stmt_quotation_delete).mappings().all()
            )
            dict_obj.update({"SourceDB": DBname})
            dict_obj.update(
                {"QuotationNumber": rows_quotation_edit[0]["QuotationNumber"]}
            )
            dict_obj.update({"BusinessName": rows_quotation_edit[0]["BusinessName"]})
            dict_obj.update({"AccountNo": rows_quotation_edit[0]["AccountNo"]})
            dict_obj.update({"QuotationID": QuotationID})
            dict_obj.update(
                {"Total": f"${round(rows_quotation_edit[0]['QuotationTotal'], 2)}"}
            )
            dict_obj.update({"Total Items": f"{len(rows_quotation_delete_sum)}"})
        successfully = f"Item {rows_quotation_edit[0]['QuotationsDetails_ProductDescription']} successfully deleted"
        return_list = "ok"

        response = self.templates.TemplateResponse(
            "edit_quotation.html",
            {
                "request": request,
                "model": model,
                "return_list": return_list,
                "update": successfully,
                "obj": dict_obj,
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def print_quotation(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "list_quotation"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        query_print_quotation = dict(parse_qsl(urlsplit(str(request.url)).query))
        user_account = request.state.user["name"]
        statususer = request.state.user["statususer"].strip().lower()
        adata = [
            "New Quotation",
        ]
        model11 = self._find_model_from_identity("quotations2_tbl")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        quotationdetails_dest_dict: Dict[int, int] = {}
        quotationdetails_dest_error_dict: Dict[int, int] = {}
        quotationdetails_dest_error_list = []
        successfully = ""
        answ_quotation_items_dict = {}
        QuotationID = query_print_quotation["QuotationID"]
        DBname = query_print_quotation["DBname"]
        QuotationNumber = query_print_quotation["QuotationNumber"]
        with Session(engine[engine_nick[DBname]]) as session:
            query_quotation = (
                select(
                    Quotations_tbl.__table__.columns,
                    Employees_tbl.FirstName,
                    Terms_tbl.TermDescription,
                    QuotationsDetails_tbl.__table__.columns,
                )
                .join(
                    Employees_tbl,
                    Quotations_tbl.SalesRepID == Employees_tbl.EmployeeID,
                )
                .join(
                    Terms_tbl,
                    Quotations_tbl.TermID == Terms_tbl.TermID,
                )
                .join(
                    QuotationsDetails_tbl,
                    Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                )
                .where(Quotations_tbl.QuotationNumber == QuotationNumber)
            )
            answ_quotation = session.execute(query_quotation).mappings().all()
            pdf_create = create_pdf_1("Quotation", answ_quotation, DBname, *adata)
            file_list: list[str] = os.listdir(os.path.abspath(os.getcwd()))
            for i in file_list:
                if i.split(".")[-1] == "pdf":
                    if i == pdf_create:
                        continue
                    else:
                        os.remove(i)
            async with aiofiles.open(pdf_create, "rb") as f:
                contents = await f.read()
            base64_string = base64.b64encode(contents).decode("utf-8")
        response = self.templates.TemplateResponse(
            "list_all_quotation.html",
            {
                "request": request,
                "model": model,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "obj": {},
                "menu": menu(request),
                "pdfFile": base64_string,
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def send_email(self, request: Request) -> Response:
        response = await send_invoice_email(request=request)

        return response
    
    async def print_invoice(self, request: Request) -> Response:
        if request.method != "POST":
            return JSONResponse({"error": "Invalid method"}, status_code=405)
        form = await request.form()
        data = dict(form)

        invoice_id = data["InvoiceID"]
        invoice_number = data["InvoiceNumber"]
        db_name = data["DBname"]
        user = request.state.user["name"]
        adata = ["New Invoice", user, f"Invoice#: {invoice_number}", "Fcs"]
        invoice_data = []
        invoice_status = ""

        with Session(engine[db_name]) as session:
            subquery_sales_rep = select(Employees_tbl.FirstName).where(
                Invoices_tbl.SalesRepID == Employees_tbl.EmployeeID
            ).scalar_subquery()

            query = (
                select(
                    Invoices_tbl.__table__.columns,
                    subquery_sales_rep.label("FirstName"),
                    Terms_tbl.TermDescription,
                    InvoicesDetails_tbl.__table__.columns,
                )
                .join(Terms_tbl, Invoices_tbl.TermID == Terms_tbl.TermID)
                .join(InvoicesDetails_tbl, Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID)
                .where(Invoices_tbl.InvoiceID == invoice_id)
            )

            # GET Term Description using TermID.
            invoice_data = session.execute(query).mappings().all()
            term_description = session.execute(
                select(
                    Terms_tbl.TermDescription
                ).where(
                    Terms_tbl.TermID == invoice_data[0]["TermID"]
                )
            ).scalar()

        sales_rep = invoice_data[0]["FirstName"] if invoice_data[0]["FirstName"] else "Unknown"
        adata.append(sales_rep)
        adata.append(invoice_data[0]["TermDescription"])
        pdf_file_name = create_invoice_pdf(
            list_items=invoice_data,
            db_name=db_name,
            invoice_number=invoice_number,
            invoice_date=invoice_data[0]["InvoiceDate"].strftime("%Y-%m-%d") if isinstance(invoice_data[0]["InvoiceDate"], datetime.datetime) else str(invoice_data[0]["InvoiceDate"]),
            business_name=invoice_data[0]["BusinessName"],
            sales_rep=sales_rep,
            producer="Fcs",
            term_description=term_description,
        )

        for file in os.listdir(os.getcwd()):
            if file.endswith(".pdf") and file != pdf_file_name:
                os.remove(file)

        async with aiofiles.open(pdf_file_name, "rb") as f:
            pdf_content = await f.read()
        encoded_pdf = base64.b64encode(pdf_content).decode("utf-8")

        response_data = {
            "data_file_invoice": [
                {
                    "pdfFile": encoded_pdf,
                    "status_invoice": invoice_status,
                    "error": 0,
                    "error_info": "",
                }
            ]
        }

        response = JSONResponse(response_data)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def print_quotation1(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            identity = request.path_params.get("identity")
            identity1 = "quotation"
            model = self._find_model_from_identity(identity)
            if not model.is_accessible(request):
                return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            QuotationNumber = dict_form["QuotationNumber"]
            ua = request.state.user["name"]
            adata = ["New Quotation", ua, f"Quotation#: {QuotationNumber}", "Fcs"]
            query_print_quotation = dict(parse_qsl(urlsplit(str(request.url)).query))
            model11 = self._find_model_from_identity("quotations2_tbl")
            get_all_actions = await model11.get_all_actions(request)
            config_model = await model11._configs(request)
            quotationdetails_dest_dict: Dict[int, int] = {}
            quotationdetails_dest_error_dict: Dict[int, int] = {}
            quotationdetails_dest_error_list = []
            successfully = ""
            answ_quotation_items_dict = {}
            QuotationID = dict_form["QuotationID"]
            DBname = dict_form["DBname"]
            SetToProgress = dict_form["SetToProgress"]
            with Session(engine[DBname]) as session:
                printchq = select(Employees_tbl.FirstName).where(
                    Quotations_tbl.SalesRepID == Employees_tbl.EmployeeID
                )
                query_quotation = (
                    select(
                        Quotations_tbl.__table__.columns,
                        printchq.label("FirstName"),
                        Terms_tbl.TermDescription,
                        QuotationsDetails_tbl.__table__.columns,
                    )
                    .join(
                        Terms_tbl,
                        Quotations_tbl.TermID == Terms_tbl.TermID,
                    )
                    .join(
                        QuotationsDetails_tbl,
                        Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                    )
                    .where(Quotations_tbl.QuotationID == QuotationID)
                    .order_by(
                        case(
                            (QuotationsDetails_tbl.ProductDescription.like('Shipping%'), 1),
                            else_=0
                        ),
                        QuotationsDetails_tbl.ProductDescription
                    )
                )
                answ_quotation = session.execute(query_quotation).mappings().all()

            # Enrich quotation items with bin locations from DB1
            enriched_quotation = []
            for item in answ_quotation:
                item_dict = dict(item)
                item_dict["BinLocation"] = get_bin_locations(item_dict.get("ProductUPC", ""))
                enriched_quotation.append(item_dict)
            answ_quotation = enriched_quotation

            if answ_quotation[0]["FirstName"] == None:
                FirstName = "Unknown"
            else:
                FirstName = answ_quotation[0]["FirstName"]
            adata.append(FirstName)
            adata.append(answ_quotation[0]["TermDescription"])
            with Session(engine["DB_admin"]) as session:
                query_checkactivequotations = select(
                    QuotationsStatus.__table__.columns
                ).filter_by(Dop1=QuotationID)
                answ_checkactivequotations = (
                    session.execute(query_checkactivequotations).mappings().all()
                )
                Qstatus = answ_checkactivequotations[0]["Status"]
                if SetToProgress == "1" and Qstatus == "New":
                    for i in answ_quotation:
                        query_set_progress = (
                            insert(QuotationsInProgress)
                            .values(
                                StartDate=time_now_5h,
                                Packer=engine_db_nick_name[DBname],
                                SourceDB=engine_db_nick_name[DBname],
                                Status="In Progress",
                                QuotationNumber=QuotationNumber,
                                AccountNo=i["AccountNo"],
                                SalesRepID=i["SalesRepID"],
                                ProductDescription=i["ProductDescription"],
                                ProductUPC=i["ProductUPC"],
                                ProductSKU=i["ProductSKU"],
                                Qty=i["Qty"],
                                CateID=i["CateID"],
                                SubCateID=i["SubCateID"],
                                tempField1=i["QuotationID"],
                            )
                            .returning(
                                QuotationsInProgress.id,
                            )
                        )
                        answ_query_set_progress = (
                            session.execute(query_set_progress).mappings().all()
                        )
                    stmt_update_qs = (
                        update(QuotationsStatus)
                        .values(
                            LastUpdate=time_now_5h,
                            Status="In Progress",
                        )
                        .where(QuotationsStatus.Dop1 == QuotationID)
                    )
                    answ_update_qs = session.execute(stmt_update_qs)
                session.commit()

            pdf_create = create_pdf_1("Quotation", answ_quotation, DBname, *adata)
            file_list: list[str] = os.listdir(os.path.abspath(os.getcwd()))
            for i in file_list:
                if i.split(".")[-1] == "pdf":
                    if i == pdf_create:
                        continue
                    else:
                        os.remove(i)
            async with aiofiles.open(pdf_create, "rb") as f:
                contents = await f.read()
            pdfFile = base64.b64encode(contents).decode("utf-8")
            fqstatus = ""
            with Session(engine["DB_admin"]) as session:
                query_checkactivequotations = select(
                    QuotationsStatus.__table__.columns
                ).filter_by(Dop1=QuotationID)
                answ_checkactivequotations = (
                    session.execute(query_checkactivequotations).mappings().all()
                )
                fqstatus = answ_checkactivequotations[0]["Status"]
        dict_answ = {
            "data_file_quotation": [
                {
                    "pdfFile": pdfFile,
                    "status_quotation": fqstatus,
                    "error": 0,
                    "error_info": "",
                },
            ]
        }
        response = JSONResponse(dict_answ)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def converttoinvoice(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            time_now_5h_min = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%m-%d-%Y %H:%M:%S")
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d 00:00:00")
            db_nick_i = SEARCH_IN_DICT_VALUE_RETURN_KEY(
                engine_nick, dict_form["DBname"]
            )
            quotationdetails_dest_dict: Dict[int, int] = {}
            quotationdetails_dest_error_dict: Dict[int, int] = {}
            quotationdetails_dest_error_list = []
            successfully = ""
            shipVia = 123
            trackingNo = ""
            shippingCost = 777888
            notes = ""
            answ_quotation_items_dict = {}
            if "shipVia" not in dict_form:
                dict_form.update(
                    {
                        "shipVia": 55444,
                        "trackingNo": "testtrackingNo",
                        "shippingCost": 999,
                        "notes": "testnotes",
                    },
                )
            if "invoiceType" not in dict_form:
                dict_form.update(
                    {
                        "invoiceType": "",
                    },
                )
            QuotationNumber = dict_form["QuotationNumber"]
            with Session(engine[dict_form["DBname"]]) as session:
                stmt_InvoiceNumber = select(
                    Invoices_tbl.AccountNo,
                    Invoices_tbl.SalesRepID,
                    Invoices_tbl.InvoiceType,
                    Invoices_tbl.InvoiceNumber,
                    Invoices_tbl.BusinessName,
                    Invoices_tbl.InvoiceID,
                    Invoices_tbl.Void,
                ).order_by(Invoices_tbl.InvoiceID.desc())
                answ_InvoiceNumber = (
                    session.execute(stmt_InvoiceNumber)
                    .mappings()
                    .all()[0]["InvoiceNumber"]
                )
                new_InvoiceNumber = int(answ_InvoiceNumber) + 1
                query_quotation = select(Quotations_tbl.__table__.columns).filter_by(
                    QuotationID=dict_form["QuotationID"]
                )
                answ_quotation_number = (
                    session.execute(query_quotation).mappings().all()
                )
                QuotationID = answ_quotation_number[0]["QuotationID"]
                query_QuotationsDetails = select(
                    QuotationsDetails_tbl.__table__.columns
                ).filter_by(QuotationID=QuotationID)
                answ_QuotationsDetails = (
                    session.execute(query_QuotationsDetails).mappings().all()
                )
                query_QuotationsDetails_qty = select(
                    func.sum(QuotationsDetails_tbl.Qty).label("QuotationsDetails_qty")
                ).filter_by(QuotationID=QuotationID)
                answer_QuotationsDetails_qty = (
                    session.execute(query_QuotationsDetails_qty)
                    .mappings()
                    .all()[0]["QuotationsDetails_qty"]
                )
                inviceq = select(Employees_tbl.FirstName).where(
                    Quotations_tbl.SalesRepID == Employees_tbl.EmployeeID
                )
                query_employees = select(
                    inviceq.label("FirstName"),
                ).where(Quotations_tbl.QuotationID == QuotationID)
                answer_employees = session.execute(query_employees).mappings().all()
                if answer_employees[0]["FirstName"] == None:
                    FirstNamech = "unknown"
                else:
                    FirstNamech = answer_employees[0]["FirstName"].strip().lower()

                quotationdetails_dict = dict(
                    (i["ProductUPC"], i["Qty"]) for i in answ_QuotationsDetails
                )
                quotationdetails_all_dict = dict(
                    (i["ProductUPC"], i) for i in answ_QuotationsDetails
                )
                quotationdetails_descr_dict = dict(
                    (i["ProductUPC"], i["ProductDescription"])
                    for i in answ_QuotationsDetails
                )
                quotation_dict = dict(
                    (i["QuotationID"], i) for i in answ_quotation_number
                )
                with Session(engine["DB1"]) as session1:
                    for i1 in quotationdetails_dict:

                        query_quotation_items = select(Items_tbl.QuantOnHand).filter_by(
                            ProductUPC=i1
                        )
                        answ_quotation_items = (
                            session1.execute(query_quotation_items).mappings().all()
                        )
                        if answ_quotation_items:
                            for i2 in range(len(answ_quotation_items)):
                                quotationdetails_dest_dict[i1] = (
                                    answ_quotation_items[i2]["QuantOnHand"]
                                    - quotationdetails_dict[i1]
                                )
                        else:
                            quotationdetails_dest_error_list.append(
                                f"In invoice {new_InvoiceNumber} not added: Description - {quotationdetails_descr_dict[i1]} UPC - {i1}"
                            )
                if not quotationdetails_dest_error_list:
                    successfully = f"Successfully create Invoice {new_InvoiceNumber}"
                stmt = (
                    insert(Invoices_tbl)
                    .values(
                        InvoiceNumber=new_InvoiceNumber,
                        InvoiceDate=time_now_5h,
                        InvoiceTitle=answ_quotation_number[0]["QuotationTitle"],
                        CustomerID=answ_quotation_number[0]["CustomerID"],
                        BusinessName=answ_quotation_number[0]["BusinessName"],
                        AccountNo=answ_quotation_number[0]["AccountNo"],
                        PoNumber=answ_quotation_number[0]["PoNumber"],
                        ShipDate=time_now_5h,
                        Shipto=answ_quotation_number[0]["Shipto"],
                        ShipAddress1=answ_quotation_number[0]["ShipAddress1"],
                        ShipAddress2=answ_quotation_number[0]["ShipAddress2"],
                        ShipContact=answ_quotation_number[0]["ShipContact"],
                        ShipCity=answ_quotation_number[0]["ShipCity"],
                        ShipState=answ_quotation_number[0]["ShipState"],
                        ShipZipCode=answ_quotation_number[0]["ShipZipCode"],
                        ShipPhoneNo=answ_quotation_number[0]["ShipPhoneNo"],
                        TermID=answ_quotation_number[0]["TermID"],
                        SalesRepID=answ_quotation_number[0]["SalesRepID"],
                        ShipperID=dict_form["shipVia"],
                        TrackingNo=dict_form["trackingNo"],
                        Notes=dict_form["notes"],
                        InvoiceType=dict_form["invoiceType"],
                        ShippingCost=dict_form["shippingCost"],
                        TotQtyOrd=answer_QuotationsDetails_qty,
                        TotQtyShp=answer_QuotationsDetails_qty,
                        NoLines=len(answ_QuotationsDetails),
                        InvoiceSubtotal=answ_quotation_number[0]["QuotationTotal"],
                        TotalTaxes=answ_quotation_number[0]["TotalTaxes"],
                        InvoiceTotal=answ_quotation_number[0]["QuotationTotal"],
                        Header=answ_quotation_number[0]["Header"],
                        Footer=answ_quotation_number[0]["Footer"],
                    )
                    .returning(
                        Invoices_tbl.__table__.columns,
                    )
                )
                rows_create_invoice = session.execute(stmt).mappings().all()
                new_invoice_id = rows_create_invoice[0]["InvoiceID"]
                stmt_update_Quotations = (
                    update(Quotations_tbl)
                    .values(AutoOrderNo=new_InvoiceNumber)
                    .filter_by(QuotationID=QuotationID)
                )
                rows_update_Quotations = session.execute(stmt_update_Quotations)
                for i in answ_QuotationsDetails:
                    ProductUPC = i["ProductUPC"]
                    QtyShipped = i["Qty"]
                    ProductSKU = i["ProductSKU"]
                    ProductDescription = i["ProductDescription"]
                    stmt_create_InvoicesDetails = (
                        insert(InvoicesDetails_tbl)
                        .values(
                            InvoiceID=new_invoice_id,
                            CateID=i["CateID"],
                            SubCateID=i["SubCateID"],
                            UnitDesc=i["UnitDesc"],
                            UnitQty=i["UnitQty"],
                            ProductID=i["ProductID"],
                            ProductSKU=ProductSKU,
                            ProductUPC=ProductUPC,
                            ProductDescription=ProductDescription,
                            ItemSize=i["ItemSize"],
                            LineMessage=i["LineMessage"],
                            UnitPrice=i["UnitPrice"],
                            OriginalPrice=i["OriginalPrice"],
                            RememberPrice=i["RememberPrice"],
                            UnitCost=i["UnitCost"],
                            Discount=i["Discount"],
                            ds_Percent=i["ds_Percent"],
                            QtyShipped=QtyShipped,
                            QtyOrdered=i["Qty"],
                            ItemWeight=i["ItemWeight"],
                            ExtendedPrice=i["ExtendedPrice"],
                            ExtendedDisc=i["ExtendedDisc"],
                            ExtendedCost=i["ExtendedCost"],
                            PromotionID=i["PromotionID"],
                            PromotionLine=i["PromotionLine"],
                            PromotionDescription=i["PromotionDescription"],
                            PromotionAmount=i["PromotionAmount"],
                            ActExtendedPrice=i["ActExtendedPrice"],
                            SPPromoted=i["SPPromoted"],
                            SPPromotionDescription=i["SPPromotionDescription"],
                            Taxable=i["Taxable"],
                            ItemTaxID=i["ItemTaxID"],
                            Catch=i["Catch"],
                            Flag=i["Flag"],
                        )
                        .returning(
                            InvoicesDetails_tbl.LineID,
                        )
                    )
                    rows_create_InvoicesDetails = (
                        session.execute(stmt_create_InvoicesDetails).mappings().all()
                    )
                    if dict_form["DBname"] == "DB1":
                        if ProductUPC in list_ship:
                            continue
                        stmt_checkinvertory = select(
                            Items_tbl.ProductUPC,
                            Items_tbl.QuantOnHand,
                        ).where(
                            and_(
                                Items_tbl.Discontinued == 0,
                                Items_tbl.ProductUPC == ProductUPC,
                            )
                        )
                        rows_checkinvertory = (
                            session.execute(stmt_checkinvertory).mappings().all()
                        )
                        if rows_checkinvertory:
                            qtydb1 = int(rows_checkinvertory[0]["QuantOnHand"]) - int(
                                QtyShipped
                            )
                        stmt_Items_tbl = (
                            update(Items_tbl)
                            .values(
                                QuantOnHand=qtydb1,
                            )
                            .filter_by(ProductUPC=ProductUPC)
                        )
                        rows_Items_tbl = session.execute(stmt_Items_tbl)
                        with Session(engine["DB_admin"]) as session4:
                            stmt = (
                                insert(QuotationDetails)
                                .values(
                                    QuotationNumber=QuotationNumber,
                                    InvoiceNumber=new_InvoiceNumber,
                                    DateCreate=time_now_5h_min,
                                    FieldDop_1=db_nick_i,
                                    FieldDop_2="Convert_to_Invoice_S2S",
                                    FieldDop_3=int(
                                        rows_checkinvertory[0]["QuantOnHand"]
                                    ),
                                    FieldDop_4=qtydb1,
                                    ProductDescription=ProductDescription,
                                    ProductSKU=ProductSKU,
                                    ProductUPC=ProductUPC,
                                    QTY=int(QtyShipped) * -1,
                                    FlagOrder=True,
                                )
                                .returning(
                                    QuotationDetails.id,
                                )
                            )
                            rows = session4.execute(stmt).mappings().all()
                            session4.commit()
                session.commit()
            with Session(engine["DB_admin"]) as session:
                stmt_delete = delete(QuotationDetails).where(
                    and_(
                        QuotationDetails.QuotationNumber
                        == dict_form["QuotationNumber"],
                        QuotationDetails.InvoiceNumber == None,
                    )
                )
                answ_delete = session.execute(stmt_delete)
                session.commit()
            with Session(engine["DB_admin"]) as session:
                BusinessName = answ_quotation_number[0]["BusinessName"]
                SalesRepresentative = FirstNamech
                QuotationNumber = dict_form["QuotationNumber"]
                stmt_delete = delete(QuotationsInProgress).where(
                    QuotationsInProgress.tempField1 == QuotationID
                )
                answ_delete = session.execute(stmt_delete)
                query_check_Quotation_admin = select(
                    Quotation.__table__.columns
                ).filter_by(Description=QuotationID)
                rows_check_Quotation_admin = (
                    session.execute(query_check_Quotation_admin).mappings().all()
                )
                if rows_check_Quotation_admin:
                    stmt_Quotation_admin = (
                        update(Quotation)
                        .values(
                            InvoiceNumber=new_InvoiceNumber,
                            LastUpdate=time_now_5h,
                            FlagOrder=True,
                        )
                        .filter_by(Description=QuotationID)
                    )
                    rows_Quotation_admin = session.execute(stmt_Quotation_admin)
                else:
                    stmt_Quotation_admin = (
                        insert(Quotation)
                        .values(
                            QuotationNumber=dict_form["QuotationNumber"],
                            SalesRepresentative=SalesRepresentative.replace("'", "''"),
                            BusinessName=BusinessName.replace("'", "''"),
                            Status="RESERVED",
                            DateCreate=time_now_5h,
                            LastUpdate=time_now_5h,
                            SourceDB=dict_form["DBname"],
                            InvoiceNumber=new_InvoiceNumber,
                            FlagOrder=True,
                            Description=QuotationID,
                        )
                        .returning(
                            Quotation.id,
                        )
                    )
                    rows_Quotation_admin = (
                        session.execute(stmt_Quotation_admin).mappings().all()
                    )
                for i in quotationdetails_dest_dict:
                    ProductDescription = quotationdetails_descr_dict[i]
                    QTY = quotationdetails_dict[i]
                    ProductSKU = quotationdetails_all_dict[i]["ProductSKU"]
                    ProductUPC = quotationdetails_all_dict[i]["ProductUPC"]
                    QuotationNumber = dict_form["QuotationNumber"]
                    with Session(engine["DB1"]) as sessiondb:
                        if quotationdetails_dest_dict[i] < 0:
                            quotationdetails_dest_error_list.append(
                                f"Оut of stock -- Description: {quotationdetails_descr_dict[i]} UPC: {i} Quantity: {quotationdetails_dest_dict[i]}"
                            )
                stmt_update_qs = (
                    update(QuotationsStatus)
                    .values(
                        LastUpdate=time_now_5h_min,
                        Status="CONVERTED",
                    )
                    .where(QuotationsStatus.Dop1 == QuotationID)
                )
                answ_update_qs = session.execute(stmt_update_qs)
                session.commit()
            dict_answ = {
                "data_converttoinvoice": [
                    {
                        "invoicenumber": new_InvoiceNumber,
                        "error": 0,
                        "error_info": "",
                    },
                ]
            }
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def updatestock(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            time_now_5h_min = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%m-%d-%Y %H:%M:%S")
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            dict_answ = {
                "data_updatestock": {
                    "items": [],
                }
            }
            error: int = 0
            error_info: str = str()
            with Session(engine["DB1"]) as session:
                for i in json.loads(dict_form["items"]):
                    ProductUPC = i["UPC"]
                    ProductSKU = i["SKU"]
                    checkinvertor_dict_temp: dict[str:str] = {
                        "SKU": ProductSKU,
                        "UPC": ProductUPC,
                    }
                    stmt_checkinvertory = select(
                        Items_tbl.ProductUPC,
                        Items_tbl.ProductSKU,
                        Items_tbl.QuantOnHand,
                    ).where(
                        and_(
                            Items_tbl.Discontinued == 0,
                            Items_tbl.ProductUPC == ProductUPC,
                        )
                    )
                    rows_checkinvertory = (
                        session.execute(stmt_checkinvertory).mappings().all()
                    )
                    if rows_checkinvertory:
                        checkinvertor_dict_temp.update(
                            {
                                "Stock": rows_checkinvertory[0]["QuantOnHand"],
                            }
                        )
                    else:
                        checkinvertor_dict_temp.update({"Stock": 0})
                    dict_answ["data_updatestock"]["items"].append(
                        checkinvertor_dict_temp
                    )
            dict_answ["data_updatestock"].update(
                {
                    "error": error,
                    "error_info": error_info,
                }
            )
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def items_massupdate(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            time_now_5h_min = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%m-%d-%Y %H:%M:%S")
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d")
            dict_answ = {"data_massupdate": {}}
            error: int = 0
            error_info: str = str()
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            with Session(engine[dict_form["DBname"]]) as session:
                with Session(engine["DB_admin"]) as session1:
                    for i in json.loads(dict_form["items"]):
                        ProductUPC = i["UPC"]
                        ProductSKU = i["SKU"]
                        ProductDescription = i["Description"]
                        UnitPrice = float(i["UnitPrice"])
                        UnitCost = float(i["UnitCost"])
                        Discontinued = i["Discontinued"]
                        UnitPriceC = float(i["DeliveryB"])

                        stmt_Items_tbl = select(
                            Items_tbl.__table__.columns,
                        ).where(Items_tbl.ProductUPC == ProductUPC)

                        answ_Items_tbl = (
                            session.execute(stmt_Items_tbl).mappings().all()
                        )
                        old_UnitPrice = float(answ_Items_tbl[0]["UnitPrice"])
                        old_UnitCost = float(answ_Items_tbl[0]["UnitCost"])
                        old_Discontinued = answ_Items_tbl[0]["Discontinued"]
                        old_UnitPriceC = float(answ_Items_tbl[0]["UnitPriceC"])

                        if old_Discontinued == Discontinued:
                            UpdateType = "Price"
                        else:
                            UpdateType = "Discontinued"

                        stmt_ManualInventoryUpdate = (
                            insert(ManualInventoryUpdate)
                            .values(
                                DateCreated=time_now_5h_min,
                                Username=user_account,
                                UserStatus=statususer,
                                UpdateType=UpdateType,
                                ProductSKU=ProductSKU,
                                ProductUPC=ProductUPC,
                                ProductDescription=ProductDescription.replace(
                                    "'", "''"
                                ),
                                OldPrice=old_UnitPrice,
                                NewPrice=UnitPrice,
                                DiffPrice=UnitPrice - old_UnitPrice,
                                OldCost=old_UnitCost,
                                NewCost=UnitCost,
                                DiffCost=UnitCost - old_UnitCost,
                                OldPriceB=old_UnitPriceC,
                                NewPriceB=UnitPriceC,
                                DiffPriceB=UnitPriceC - old_UnitPriceC,
                            )
                            .returning(
                                ManualInventoryUpdate.id,
                            )
                        )

                        rows_ManualInventoryUpdate = (
                            session1.execute(stmt_ManualInventoryUpdate)
                            .mappings()
                            .all()
                        )
                        stmt_massupdate = (
                            update(Items_tbl)
                            .values(
                                UnitPrice=UnitPrice,
                                UnitCost=UnitCost,
                                Discontinued=Discontinued,
                                UnitPriceC=UnitPriceC,
                                ExpDate=time_now_5h,
                            )
                            .filter_by(ProductUPC=ProductUPC)
                        )
                        rows_massupdate = session.execute(stmt_massupdate)

                    session1.commit()
                    session.commit()

            dict_answ["data_massupdate"].update(
                {
                    "error": error,
                    "error_info": error_info,
                }
            )
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def getpolist(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            dict_answ = {"data_getpolist": []}
            error: int = 0
            error_info: str = str()
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            isCommitAllowed = checkcomituser(statususer)
            with Session(engine[dict_form["DB"]]) as session:
                stmt_PurchaseOrders_tbl = select(
                    PurchaseOrders_tbl.__table__.columns,
                    Suppliers_tbl.BusinessName.label("SuppliersBusinessName"),
                ).join(
                    Suppliers_tbl,
                    Suppliers_tbl.SupplierID == PurchaseOrders_tbl.SupplierID,
                )

                answ_PurchaseOrders = (
                    session.execute(stmt_PurchaseOrders_tbl).mappings().all()
                )
            for i in answ_PurchaseOrders:
                getpolist_dict_temp = {
                    "POID": i["PoID"],
                    "PONumber": i["PoNumber"],
                    "PODate": i["PoDate"].strftime("%m-%d-%Y"),
                    "Supplier": i["SuppliersBusinessName"],
                    "Status": i["Status"],
                    "POTotal": float(i["PoTotal"]),
                    "Notes": i["Notes"],
                }

                dict_answ["data_getpolist"].append(getpolist_dict_temp)

            dict_answ.update(
                {
                    "error": error,
                    "error_info": error_info,
                    "isCommitAllowed": isCommitAllowed,
                }
            )

            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def productDetails(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            dict_answ = {"data": []}
            error: int = 0
            error_info: str = str()
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            isCommitAllowed = checkcomituser(statususer)
            SourceDB = dict_form["DB"]
            Acno = dict_form["AccountNumber"]
            for i in json.loads(dict_form["Items"]):
                ProductUPC = i["UPC"]
                ans_dtemp: dict = dict()
                reslist = list()
                with Session(engine[SourceDB]) as session:
                    stmt_items = select(
                        Items_tbl.__table__.columns,
                    ).where(
                        Items_tbl.ProductUPC == ProductUPC,
                    )
                    answ_items = session.execute(stmt_items).mappings().all()
                    if answ_items:
                        if answ_items[0]["UnitCost"] == None:
                            UnitCost = 0
                        else:
                            UnitCost = float(answ_items[0]["UnitCost"])

                        if answ_items[0]["UnitPrice"] == None:
                            UnitPrice = 0
                        else:
                            UnitPrice = float(answ_items[0]["UnitPrice"])

                        if answ_items[0]["UnitPriceC"] == None:
                            UnitPriceC = 0
                        else:
                            UnitPriceC = float(answ_items[0]["UnitPriceC"])

                        ans_dtemp.update(
                            {"ProductDescription": answ_items[0]["ProductDescription"]}
                        )
                        ans_dtemp.update({"Cost": UnitCost})
                        ans_dtemp.update({"Standard": UnitPrice})
                        ans_dtemp.update({"DeliveryB": UnitPriceC})
                    stmt_chec = (
                        select(
                            Invoices_tbl.InvoiceDate,
                            InvoicesDetails_tbl.UnitPrice,
                            InvoicesDetails_tbl.ProductUPC,
                        )
                        .join(
                            Invoices_tbl,
                            Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID,
                        )
                        .where(
                            and_(
                                Invoices_tbl.Void == 0,
                                Invoices_tbl.InvoiceTitle not in ch_lis,
                                Invoices_tbl.AccountNo == Acno,
                                InvoicesDetails_tbl.ProductUPC == ProductUPC,
                                InvoicesDetails_tbl.RememberPrice == 1,
                            )
                        )
                        .order_by(Invoices_tbl.InvoiceNumber.desc())
                    )
                    rows_chec = session.execute(stmt_chec).mappings().all()
                    if rows_chec:
                        ans_dtemp.update({"Custom": float(rows_chec[0]["UnitPrice"])})
                    else:
                        ans_dtemp.update({"Custom": 0})
                    query_po = (
                        select(
                            PurchaseOrders_tbl.__table__.columns,
                            PurchaseOrdersDetails_tbl.__table__.columns,
                        )
                        .join(
                            PurchaseOrdersDetails_tbl,
                            PurchaseOrdersDetails_tbl.PoID == PurchaseOrders_tbl.PoID,
                        )
                        .where(
                            and_(
                                PurchaseOrders_tbl.Status == 0,
                                PurchaseOrdersDetails_tbl.ProductUPC == ProductUPC,
                            )
                        )
                    )
                    rows_po = session.execute(query_po).mappings().all()
                    if rows_po:
                        ans_dtemp.update(
                            {"Incoming": sum([i5["QtyOrdered"] for i5 in rows_po])}
                        )
                    else:
                        ans_dtemp.update({"Incoming": 0})

                    stmt_chec_dop = (
                        select(
                            Invoices_tbl.InvoiceDate,
                            Invoices_tbl.InvoiceTitle,
                            InvoicesDetails_tbl.ProductUPC,
                            InvoicesDetails_tbl.QtyShipped,
                            InvoicesDetails_tbl.UnitPrice,
                        )
                        .join(
                            Invoices_tbl,
                            Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID,
                        )
                        .where(
                            and_(
                                Invoices_tbl.Void == 0,
                                Invoices_tbl.InvoiceTitle not in ch_lis,
                                Invoices_tbl.AccountNo == Acno,
                                InvoicesDetails_tbl.ProductUPC == ProductUPC,
                            )
                        )
                        .order_by(Invoices_tbl.InvoiceNumber.desc())
                    )
                    rows_chec_dop = session.execute(stmt_chec_dop).mappings().all()
                    if rows_chec_dop:
                        ans_dtemp.update(
                            {"LastSaleQty": rows_chec_dop[0]["QtyShipped"]}
                        )
                        ans_dtemp.update(
                            {
                                "LastSaleDate": rows_chec_dop[0][
                                    "InvoiceDate"
                                ].strftime("%m/%d/%Y")
                            }
                        )
                        ans_dtemp.update(
                            {"LastPriceLevel": rows_chec_dop[0]["InvoiceTitle"]}
                        )
                        ans_dtemp.update(
                            {"LastPrice": rows_chec_dop[0]["UnitPrice"]}
                        )
                    else:
                        ans_dtemp.update({"LastSaleQty": "-"})
                        ans_dtemp.update({"LastSaleDate": "-"})
                        ans_dtemp.update({"LastPriceLevel": "-"})
                        ans_dtemp.update({"LastPrice": "-"})
                with Session(engine["DB1"]) as session:
                    stmt_items = select(
                        Items_tbl.__table__.columns,
                    ).where(
                        Items_tbl.ProductUPC == ProductUPC,
                    )
                    answ_items = session.execute(stmt_items).mappings().all()
                    if answ_items:
                        ans_dtemp.update({"Stock": float(answ_items[0]["QuantOnHand"])})
                    else:
                        ans_dtemp.update({"Stock": 0})
                with Session(engine[engine_nick["Shipper Platform"]]) as session3:
                    stmt_check_ship = (
                        select(
                            pick_lists.cdate,
                            pick_list_products.__table__.columns,
                        )
                        .join(
                            pick_lists,
                            pick_list_products.id_pick_list == pick_lists.id,
                        )
                        .where(
                            and_(
                                pick_lists.is_printed == 1,
                                pick_list_products.barcode == ProductUPC,
                            )
                        )
                    )
                    answ_check_ship = session3.execute(stmt_check_ship).mappings().all()
                if answ_check_ship:
                    reslist.append(answ_check_ship[0]["amount"])
                with Session(engine["DB_admin"]) as session:
                    stmt_items_pr = select(
                        QuotationsInProgress.__table__.columns,
                    ).where(
                        and_(
                            QuotationsInProgress.ProductUPC == ProductUPC,
                            QuotationsInProgress.Status == "In Progress",
                        )
                    )
                    answ_items_pr = session.execute(stmt_items_pr).mappings().all()
                if answ_items_pr:
                    reslist.append(answ_items_pr[0]["Qty"])
                ans_dtemp.update({"Reserved": sum(reslist)})

                dict_answ["data"].append(ans_dtemp)
            dict_answ.update(
                {
                    "error": error,
                    "error_info": error_info,
                }
            )
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def commitpo(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            dict_answ = {}
            error: int = 0
            error_info: str = str()
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            isCommitAllowed = checkcomituser(statususer)
            PoNumber = dict_form["PoNumber"]

            with Session(engine[dict_form["DB"]]) as session:
                stmt_PurchaseOrders_tbl = select(
                    PurchaseOrders_tbl.__table__.columns,
                ).filter_by(PoNumber=PoNumber)
                answ_PurchaseOrders = (
                    session.execute(stmt_PurchaseOrders_tbl).mappings().all()
                )
                PoID = answ_PurchaseOrders[0]["PoID"]
                if answ_PurchaseOrders[0]["Status"] == 1:
                    dict_answ = {
                        "data": [],
                        "error": 1,
                        "error_info": "Purchase Order already commit",
                    }
                    response = JSONResponse(dict_answ)
                    response.headers["Cache-Control"] = (
                        "no-store, no-cache, must-revalidate, max-age=0"
                    )
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response

                stmt_delete_quotation_sum = (
                    update(PurchaseOrders_tbl)
                    .values(
                        Status=1,
                    )
                    .where(PurchaseOrders_tbl.PoNumber == PoNumber)
                )
                answ_update_quotation_details = session.execute(
                    stmt_delete_quotation_sum
                )
                session.commit()

            dict_answ.update(
                {
                    "error": error,
                    "error_info": error_info,
                    "isCommitAllowed": isCommitAllowed,
                }
            )

            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def getpo(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            dict_answ = {
                "data_getpo": [],
            }
            error: int = 0
            error_info: str = str()
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            PoNumber = dict_form["PoNumber"]
            print(user_account, statususer, "user_account_getpooo")
            isCommitAllowed = checkcomituser(statususer)
            with Session(engine[dict_form["DBname"]]) as session:
                stmt_PurchaseOrders_tbl = (
                    select(
                        PurchaseOrders_tbl.__table__.columns,
                        PurchaseOrdersDetails_tbl.ProductSKU.label("SKU"),
                        PurchaseOrdersDetails_tbl.ProductUPC.label("UPC"),
                        PurchaseOrdersDetails_tbl.QtyOrdered.label("QTY"),
                        PurchaseOrdersDetails_tbl.UnitCost.label("UnitCost"),
                        PurchaseOrdersDetails_tbl.ProductDescription.label(
                            "ProductDescription"
                        ),
                        (
                            PurchaseOrdersDetails_tbl.QtyOrdered
                            * PurchaseOrdersDetails_tbl.UnitCost
                        ).label("Total"),
                        Suppliers_tbl.Contactname.label("Contactname"),
                        Suppliers_tbl.Phone_Number.label("Phone_Number"),
                    )
                    .join(
                        Suppliers_tbl,
                        Suppliers_tbl.SupplierID == PurchaseOrders_tbl.SupplierID,
                    )
                    .join(
                        PurchaseOrdersDetails_tbl,
                        PurchaseOrdersDetails_tbl.PoID == PurchaseOrders_tbl.PoID,
                    )
                    .where(
                        PurchaseOrders_tbl.PoNumber == PoNumber,
                    )
                )

                answ_PurchaseOrders = (
                    session.execute(stmt_PurchaseOrders_tbl).mappings().all()
                )
            for i in answ_PurchaseOrders:
                temp_po = {
                    "SKU": i["SKU"],
                    "UPC": i["UPC"],
                    "QTY": i["QTY"],
                    "Description": i["ProductDescription"],
                    "UnitCost": float(i["UnitCost"]),
                    "Total": i["Total"],
                }
                dict_answ["data_getpo"].append(temp_po)

            if answ_PurchaseOrders:
                pass
            else:
                stmt_PurchaseOrders_tbl = (
                    select(
                        PurchaseOrders_tbl.__table__.columns,
                        Suppliers_tbl.Contactname.label("Contactname"),
                        Suppliers_tbl.Phone_Number.label("Phone_Number"),
                    )
                    .join(
                        Suppliers_tbl,
                        Suppliers_tbl.SupplierID == PurchaseOrders_tbl.SupplierID,
                    )
                    .where(
                        PurchaseOrders_tbl.PoNumber == PoNumber,
                    )
                )

                answ_PurchaseOrders = (
                    session.execute(stmt_PurchaseOrders_tbl).mappings().all()
                )
            dict_answ.update(
                {
                    "POid": answ_PurchaseOrders[0]["PoID"],
                    "PONumber": answ_PurchaseOrders[0]["PoNumber"],
                    "Date": answ_PurchaseOrders[0]["PoDate"].strftime("%m/%d/%Y"),
                    "Status": answ_PurchaseOrders[0]["Status"],
                    "anum": answ_PurchaseOrders[0]["AccountNo"],
                    "bnum": answ_PurchaseOrders[0]["BusinessName"],
                    "contactname": answ_PurchaseOrders[0]["Contactname"],
                    "Notes": answ_PurchaseOrders[0]["Notes"],
                    "Phone_Number": answ_PurchaseOrders[0]["Phone_Number"],
                }
            )
            dict_answ.update(
                {
                    "isCommitAllowed": isCommitAllowed,
                }
            )
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def deletepo(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            dict_answ = {}
            error: int = 0
            error_info: str = str()
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            isCommitAllowed = checkcomituser(statususer)
            PoID = dict_form["PoID"]
            with Session(engine[dict_form["DB"]]) as session:
                stmt_delete = delete(PurchaseOrders_tbl).where(
                    PurchaseOrders_tbl.PoID == PoID
                )
                answ_delete = session.execute(stmt_delete)
                stmt_delete_det = delete(PurchaseOrdersDetails_tbl).where(
                    PurchaseOrdersDetails_tbl.PoID == PoID
                )
                answ_delete_det = session.execute(stmt_delete_det)
                session.commit()
            dict_answ.update(
                {
                    "error": error,
                    "error_info": error_info,
                    "isCommitAllowed": isCommitAllowed,
                }
            )
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def printpo(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            dict_answ = {"data_printpo": []}
            error: int = 0
            error_info: str = str()
            PoNumber = dict_form["PONumber"]
            PoID = dict_form["PoId"]
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            ua = request.state.user["name"]
            pdata = ["New Purchase Order", ua, f"Purchase Order#: {PoNumber}", "Fcs"]
            isCommitAllowed = checkcomituser(statususer)
            DBname = dict_form["DBname"]
            with Session(engine[DBname]) as session:
                query_po = (
                    select(
                        PurchaseOrders_tbl.__table__.columns,
                        PurchaseOrdersDetails_tbl.__table__.columns,
                    )
                    .join(
                        PurchaseOrdersDetails_tbl,
                        PurchaseOrdersDetails_tbl.PoID == PurchaseOrders_tbl.PoID,
                    )
                    .where(PurchaseOrders_tbl.PoID == PoID)
                )
                answ_po = session.execute(query_po).mappings().all()
                pdf_create = create_pdf_1("Purchase Order", answ_po, DBname, *pdata)
                file_list: list[str] = os.listdir(os.path.abspath(os.getcwd()))
                for i in file_list:
                    if i.split(".")[-1] == "pdf":
                        if i == pdf_create:
                            continue
                        else:
                            os.remove(i)
                async with aiofiles.open(pdf_create, "rb") as f:
                    contents = await f.read()
                pdfFile = base64.b64encode(contents).decode("utf-8")
            dict_answ = {
                "data_printpo": [
                    {
                        "pdfFile": pdfFile,
                        "error": 0,
                        "error_info": "",
                        "isCommitAllowed": isCommitAllowed,
                    },
                ]
            }
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def upload_files(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "upload_file"
        model = self._find_model_from_identity(identity)
        form = await request.form()
        filename = form["file1"].filename
        dict_xls_data: dict[str:Any] = dict()
        async with request.form() as form:
            for i in form:
                filename = form[i].filename
                contents = await form[i].read()
                dict_xls_data[filename] = contents
        contents_rb = dict_xls_data["test.xlsx"]
        base64_string = base64.b64encode(contents_rb).decode("utf-8")
        return self.templates.TemplateResponse(
            "list_upload.html",
            {
                "request": request,
                "model": model,
                "obj": {},
                "menu": menu(request),
                "pdfFile": base64_string,
            },
        )

    async def view_edit_quotation(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "list_quotation"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)

        return "ok"


    async def view_edit_quotation_1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "list_quotation"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        query_view_edit_quotation_1 = dict(parse_qsl(urlsplit(str(request.url)).query))
        model11 = self._find_model_from_identity("quotationsdetails1_tbl")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        form = await request.form()
        list_obj_detail: list[str] = list()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        with Session(
            engine[engine_nick[query_view_edit_quotation_1["DBname"]]]
        ) as session:
            stmt_quotation_edit = select(Quotations_tbl.__table__.columns).filter_by(
                QuotationNumber=query_view_edit_quotation_1["QuotationNumber"]
            )
            rows_quotation_edit = session.execute(stmt_quotation_edit).mappings().all()
            dict_obj.update({"SourceDB": query_view_edit_quotation_1["DBname"]})
            dict_obj.update(
                {"QuotationNumber": query_view_edit_quotation_1["QuotationNumber"]}
            )
            dict_obj.update({"BusinessName": rows_quotation_edit[0]["BusinessName"]})
            dict_obj.update({"AccountNo": rows_quotation_edit[0]["AccountNo"]})
            dict_obj.update(
                {"Total": f"${round(rows_quotation_edit[0]['QuotationTotal'], 2)}"}
            )
            stmt_quotation_edit_det = select(
                QuotationsDetails_tbl.__table__.columns
            ).filter_by(QuotationID=query_view_edit_quotation_1["QuotationID"])
            rows_quotation_edit_det = (
                session.execute(stmt_quotation_edit_det).mappings().all()
            )
            for i in rows_quotation_edit_det:
                dict_obj_detail: dict[str:str] = dict()
                dict_obj_detail["LineID"] = i["LineID"]
                dict_obj_detail["ProductDescription"] = i["ProductDescription"]
                dict_obj_detail["ProductSKU"] = i["ProductSKU"]
                dict_obj_detail["Qty"] = i["Qty"]
                dict_obj_detail["UnitPrice"] = f'${round(i["UnitPrice"], 2)}'
                list_obj_detail.append(dict_obj_detail)
        obj_edit = {}

        response = self.templates.TemplateResponse(
            "create_new_quotation_edit.html",
            {
                "request": request,
                "model": model,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "obj": dict_obj,
                "list_obj_detail": list_obj_detail,
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def add_quotation(self, request: Request) -> Response:
        model11 = self._find_model_from_identity("quotationsdetails1_tbl")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        url_ref: str = ""
        for i in range(len(request.scope["headers"])):
            if len(request.scope["headers"][i]) > 1:
                for i1 in request.scope["headers"][i]:
                    if isinstance(i1, bytes):
                        val_i = i1.decode()
                    else:
                        val_i = i1
                    if val_i == "referer":
                        url_ref = request.scope["headers"][i][1]
        if url_ref:
            query_update_quotation_details = dict(
                parse_qsl(urlsplit(str(url_ref)).query)
            )
        dict_obj: dict[str:str] = dict()
        with Session(
            engine[engine_nick[query_update_quotation_details["DBname"]]]
        ) as session:

            stmt_quotation_edit = (
                select(
                    Quotations_tbl.__table__.columns,
                    QuotationsDetails_tbl.LineID.label("QuotationsDetails_id"),
                    QuotationsDetails_tbl.ProductDescription.label(
                        "QuotationsDetails_ProductDescription"
                    ),
                    QuotationsDetails_tbl.ProductSKU.label(
                        "QuotationsDetails_ProductSKU"
                    ),
                )
                .join(
                    QuotationsDetails_tbl,
                    Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                )
                .where(
                    and_(
                        QuotationsDetails_tbl.QuotationID
                        == query_update_quotation_details["QuotationID"],
                    )
                )
            )
            rows_add_quotation = session.execute(stmt_quotation_edit).mappings().all()
            dict_obj.update({"SourceDB": query_update_quotation_details["DBname"]})
            dict_obj.update(
                {"QuotationNumber": rows_add_quotation[0]["QuotationNumber"]}
            )
            dict_obj.update({"BusinessName": rows_add_quotation[0]["BusinessName"]})
            dict_obj.update({"AccountNo": rows_add_quotation[0]["AccountNo"]})
            dict_obj.update(
                {"QuotationID": query_update_quotation_details["QuotationID"]}
            )
            dict_obj.update(
                {"Total": f"${round(rows_add_quotation[0]['QuotationTotal'], 2)}"}
            )
        obj_add = "ok"

        response = self.templates.TemplateResponse(
            "edit_quotation.html",
            {
                "request": request,
                "model": model11,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "obj_add": obj_add,
                "obj": dict_obj,
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def checkinvertory(self, request: Request) -> Response:
        model11 = self._find_model_from_identity("checkinvertory")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        response = self.templates.TemplateResponse(
            "checkinvertory.html",
            {
                "request": request,
                "model": model11,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "update": "You must wait a few minutes for the results to be processed",
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def errorcheckinvertory(self, request: Request) -> Response:
        model11 = self._find_model_from_identity("checkinvertory")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        DateFrom = "2024-02-19 00:00:00"
        time_now_7d = (datetime.datetime.today() + datetime.timedelta(days=5)).strftime(
            "%Y-%m-%d 00:00:00"
        )
        update_text = "You must wait a few minutes for the results Error checking"
        checkinvertory_error_str_3 = []
        checkinvertory_dates_error_str = [
            f"DateFrom: {DateFrom}",
            f"DateTo: {time_now_7d}",
        ]
        checkinvertory_error_str_2 = ""

        db_check: list[str] = [
            "PrimeWholesale",
            "RAND",
            "TStockShopify",
            "TSWShopify",
            "PWcomShopify",
            "S2S",
        ]

        with Session(engine["DB1"]) as session:
            stmt_checkinvertory = select(
                Items_tbl.ProductUPC,
                Items_tbl.ProductDescription,
            ).where(
                and_(
                    Items_tbl.Discontinued == 0,
                    Items_tbl.ReorderLevel == 7,
                )
            )
            rows_checkinvertory = session.execute(stmt_checkinvertory).mappings().all()
        with Session(engine["DB1"]) as session:
            for count, i_rows_checkinvertory in enumerate(rows_checkinvertory):
                starting_purchased: list[int] = list()
                list_db_sum: list[int] = list()
                ProductUPC = i_rows_checkinvertory["ProductUPC"]
                ProductDescription = i_rows_checkinvertory["ProductDescription"]

                stmt_start = (
                    select(
                        PurchaseOrders_tbl.PoID,
                        PurchaseOrdersDetails_tbl.ProductUPC,
                        PurchaseOrdersDetails_tbl.ProductDescription,
                        PurchaseOrdersDetails_tbl.QtyOrdered,
                    )
                    .join(
                        PurchaseOrdersDetails_tbl,
                        PurchaseOrdersDetails_tbl.PoID == PurchaseOrders_tbl.PoID,
                    )
                    .where(
                        and_(
                            PurchaseOrders_tbl.PoID == 11688,
                            PurchaseOrdersDetails_tbl.ProductUPC == ProductUPC,
                        )
                    )
                )
                rows_start = session.execute(stmt_start).mappings().all()
                if rows_start:
                    starting_purchased.append(rows_start[0]["QtyOrdered"])
                else:
                    starting_purchased.append(0)

                stmt_purchase = (
                    select(
                        PurchaseOrdersDetails_tbl.ProductUPC,
                        PurchaseOrdersDetails_tbl.ProductDescription,
                        func.sum(PurchaseOrdersDetails_tbl.QtyOrdered).label("Qty"),
                    )
                    .join(
                        PurchaseOrdersDetails_tbl,
                        PurchaseOrdersDetails_tbl.PoID == PurchaseOrders_tbl.PoID,
                    )
                    .where(
                        and_(
                            PurchaseOrders_tbl.PoDate.between(DateFrom, time_now_7d),
                            PurchaseOrdersDetails_tbl.ProductUPC == ProductUPC,
                        )
                    )
                    .group_by(
                        PurchaseOrdersDetails_tbl.ProductUPC,
                        PurchaseOrdersDetails_tbl.ProductDescription,
                    )
                    .select_from(PurchaseOrders_tbl)
                )

                rows_purchase = session.execute(stmt_purchase).mappings().all()
                if rows_purchase:
                    starting_purchased.append(rows_purchase[0]["Qty"])
                else:
                    starting_purchased.append(0)

                for i_db_check in db_check:
                    with Session(engine[engine_name_db[i_db_check]]) as session2:
                        prod_sales = (
                            select(
                                InvoicesDetails_tbl.ProductUPC,
                                InvoicesDetails_tbl.ProductDescription,
                                func.sum(InvoicesDetails_tbl.QtyShipped).label("Qty"),
                            )
                            .join(
                                Invoices_tbl,
                                Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID,
                            )
                            .group_by(
                                InvoicesDetails_tbl.ProductUPC,
                                InvoicesDetails_tbl.ProductDescription,
                            )
                        )

                        if i_db_check == "RAND":
                            prod_sales = prod_sales.where(
                                and_(
                                    Invoices_tbl.InvoiceDate.between(
                                        DateFrom, time_now_7d
                                    ),
                                    Invoices_tbl.Void == 0,
                                    InvoicesDetails_tbl.ProductUPC == ProductUPC,
                                    Invoices_tbl.AccountNo != "WHPRIMEAK",
                                    Invoices_tbl.AccountNo != "whprimeak",
                                    Invoices_tbl.AccountNo != "WHRANDSTRTS",
                                    Invoices_tbl.AccountNo != "whrandstrts",
                                    Invoices_tbl.AccountNo != "WHFCS",
                                    Invoices_tbl.AccountNo != "whfcs",
                                    Invoices_tbl.AccountNo != "WHS2S",
                                    Invoices_tbl.AccountNo != "whs2s",
                                )
                            )
                        elif i_db_check == "S2S":
                            prod_sales = prod_sales.where(
                                and_(
                                    Invoices_tbl.InvoiceDate.between(
                                        DateFrom, time_now_7d
                                    ),
                                    Invoices_tbl.Void == 0,
                                    InvoicesDetails_tbl.ProductUPC == ProductUPC,
                                    Invoices_tbl.AccountNo != "WHPRIMEAK",
                                    Invoices_tbl.AccountNo != "whprimeak",
                                    Invoices_tbl.AccountNo != "WHRAND",
                                    Invoices_tbl.AccountNo != "whrand",
                                    Invoices_tbl.AccountNo != "WHRANDSTRTS",
                                    Invoices_tbl.AccountNo != "whrandstrts",
                                    Invoices_tbl.AccountNo != "WHAV1PRIME",
                                    Invoices_tbl.AccountNo != "whav1prime",
                                    Invoices_tbl.AccountNo != "WHRANDSTRA2Z",
                                    Invoices_tbl.AccountNo != "whrandstra2z",
                                    Invoices_tbl.AccountNo != "AV1AK",
                                    Invoices_tbl.AccountNo != "av1ak",
                                )
                            )

                        else:
                            prod_sales = prod_sales.where(
                                and_(
                                    Invoices_tbl.InvoiceDate.between(
                                        DateFrom, time_now_7d
                                    ),
                                    Invoices_tbl.Void == 0,
                                    InvoicesDetails_tbl.ProductUPC == ProductUPC,
                                )
                            )

                        rows_prod_sales = session2.execute(prod_sales).mappings().all()
                        if rows_prod_sales:
                            list_db_sum.append(rows_prod_sales[0]["Qty"])
                        else:
                            list_db_sum.append(0)

                starting_purchased_sum = sum(starting_purchased)
                db_sum = sum(list_db_sum)
                with Session(engine["DB1"]) as session:
                    stmt_actual = select(
                        Items_tbl.QuantOnHand,
                    ).where(
                        and_(
                            Items_tbl.ProductUPC == ProductUPC,
                        )
                    )
                    rows_actual = session.execute(stmt_actual).mappings().all()

                rez = starting_purchased_sum - db_sum
                rez_actual = rows_actual[0]["QuantOnHand"]
                diff_rez = rez - rez_actual
                if rez != rez_actual:
                    checkinvertory_error_str = f'{ProductDescription} -- {ProductUPC} -- {" -- ".join(str(i) for i in starting_purchased)} {" -- ".join(str(i) for i in list_db_sum)}'
                    checkinvertory_error_str_1 = f'{ProductDescription} -- {ProductUPC} -- {" -- ".join(str(i) for i in starting_purchased)} {" -- ".join(str(i) for i in list_db_sum)}'
                    checkinvertory_error_str_2 = [
                        "DESCRIPTION",
                        "UPC",
                        "STARTING",
                        "PURCHASES",
                        "5STARS",
                        "RAND",
                        "TS",
                        "TSW",
                        "PRIME",
                        "FCS",
                        "CALCONHAND",
                        "ACTUAL",
                        "CALC-ACTUAL",
                    ]
                    checkinvertory_error_str_3_temp = []
                    checkinvertory_error_str_3_temp.append(ProductDescription)
                    checkinvertory_error_str_3_temp.append(ProductUPC)
                    [
                        checkinvertory_error_str_3_temp.append(i)
                        for i in starting_purchased
                    ]
                    [checkinvertory_error_str_3_temp.append(i) for i in list_db_sum]
                    checkinvertory_error_str_3_temp.append(rez)
                    checkinvertory_error_str_3_temp.append(rez_actual)
                    checkinvertory_error_str_3_temp.append(diff_rez)
                    checkinvertory_error_str_3.append(checkinvertory_error_str_3_temp)
                    update_text = ""
                if not checkinvertory_error_str_3:
                    update_text = "No Error found"

        response = self.templates.TemplateResponse(
            "checkinvertory.html",
            {
                "request": request,
                "model": model11,
                "update": update_text,
                "update_error_list": checkinvertory_error_str_3,
                "header_error_list": checkinvertory_error_str_2,
                "dates_error_list": checkinvertory_dates_error_str,
                "menu": menu(request),
            },
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def update_add_quotation(self, request: Request) -> Response:
        model11 = self._find_model_from_identity("quotationsdetails1_tbl")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        form = await request.form()
        dict_obj1 = await self.form_to_dict(
            request, form, model11, RequestAction.CREATE
        )
        url_ref: str = ""
        for i in range(len(request.scope["headers"])):
            if len(request.scope["headers"][i]) > 1:
                for i1 in request.scope["headers"][i]:
                    if isinstance(i1, bytes):
                        val_i = i1.decode()
                    else:
                        val_i = i1
                    if val_i == "referer":
                        url_ref = request.scope["headers"][i][1]
        if url_ref:
            query_update_quotation_details = dict(
                parse_qsl(urlsplit(str(url_ref)).query)
            )
        dict_obj: dict[str:str] = dict()
        obj_add: dict[str:str] = dict()

        with Session(
            engine[engine_nick[query_update_quotation_details["DBname"]]]
        ) as session:

            stmt_quotation_edit = (
                select(
                    Quotations_tbl.__table__.columns,
                    QuotationsDetails_tbl.LineID.label("QuotationsDetails_id"),
                    QuotationsDetails_tbl.ProductDescription.label(
                        "QuotationsDetails_ProductDescription"
                    ),
                    QuotationsDetails_tbl.ProductSKU.label(
                        "QuotationsDetails_ProductSKU"
                    ),
                )
                .join(
                    QuotationsDetails_tbl,
                    Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                )
                .where(
                    and_(
                        QuotationsDetails_tbl.QuotationID
                        == query_update_quotation_details["QuotationID"],
                    )
                )
            )

            rows_add_quotation = session.execute(stmt_quotation_edit).mappings().all()
            dict_obj.update({"SourceDB": query_update_quotation_details["DBname"]})
            dict_obj.update(
                {"QuotationNumber": rows_add_quotation[0]["QuotationNumber"]}
            )
            dict_obj.update({"BusinessName": rows_add_quotation[0]["BusinessName"]})
            dict_obj.update({"AccountNo": rows_add_quotation[0]["AccountNo"]})
            dict_obj.update(
                {"QuotationID": query_update_quotation_details["QuotationID"]}
            )
            dict_obj.update(
                {"Total": f"${round(rows_add_quotation[0]['QuotationTotal'], 2)}"}
            )

            obj_add["ProductDescription"] = "oiuuiuqjkj"
            obj_add["UnitPrice"] = 544

            try:
                obj = await model11.add_items_quotation(request, dict_obj1)

            except FormValidationError as exc:
                response = self.templates.TemplateResponse(
                    "edit_quotation.html",
                    {
                        "errors": exc.errors,
                        "obj": dict_obj,
                        "menu": menu(request),
                        "request": request,
                        "model": model11,
                        "_actions": get_all_actions,
                        "__js_model__": config_model,
                        "obj_add": obj_add,
                        "menu": menu(request),
                    },
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                )
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            stmt_quotation_items = select(Items_tbl.__table__.columns).filter_by(
                ProductSKU=dict_obj1["SKU"]
            )
            rows_quotation_items = (
                session.execute(stmt_quotation_items).mappings().all()
            )
            stmt_quotation_UnitDesc = select(Units_tbl.__table__.columns).filter_by(
                UnitID=str(rows_quotation_items[0]["UnitID"])
            )
            rows_quotation_UnitDesc = (
                session.execute(stmt_quotation_UnitDesc).mappings().all()
            )
            if rows_quotation_UnitDesc:
                UnitDesc = rows_quotation_UnitDesc[0]["UnitDesc"]
            else:
                UnitDesc = ""
            QuotationID = query_update_quotation_details["QuotationID"]
            stmt_quotationsdetails = (
                insert(QuotationsDetails_tbl)
                .values(
                    QuotationID=QuotationID,
                    CateID=rows_quotation_items[0]["CateID"],
                    SubCateID=rows_quotation_items[0]["SubCateID"],
                    ProductID=rows_quotation_items[0]["ProductID"],
                    ProductSKU=rows_quotation_items[0]["ProductSKU"],
                    ProductUPC=rows_quotation_items[0]["ProductUPC"],
                    ProductDescription=rows_quotation_items[0]["ProductDescription"],
                    ItemSize=rows_quotation_items[0]["ItemSize"],
                    ExpDate=ExpirationDate,
                    UnitPrice=UnitPrice,
                    OriginalPrice=UnitPrice,
                    UnitCost=rows_quotation_items[0]["UnitCost"],
                    Qty=Qty,
                    ItemWeight=rows_quotation_items[0]["ItemWeight"],
                    Discount=0,
                    ds_Percent=0,
                    ExtendedPrice=UnitPrice * Qty,
                    ExtendedCost=rows_quotation_items[0]["UnitCost"] * Qty,
                    ExtendedDisc=0,
                    PromotionID=0,
                    PromotionLine=0,
                    SPPromoted=0,
                    Taxable=0,
                    ItemTaxID=0,
                    Catch=0,
                    Flag=0,
                    ActExtendedPrice=UnitPrice * Qty,
                    UnitDesc=UnitDesc,
                )
                .returning(
                    QuotationsDetails_tbl.LineID,
                )
            )

            rows_quotationsdetails = (
                session.execute(stmt_quotationsdetails).mappings().all()
            )

        successfully = f"Item {dict_obj1['ProductDescription']} successfully added in Quotation {rows_add_quotation[0]['QuotationNumber']}"

        return self.templates.TemplateResponse(
            "edit_quotation.html",
            {
                "request": request,
                "model": model11,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "update": successfully,
                "obj": obj,
                "menu": menu(request),
            },
        )

    async def edit_quotation(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "edit_quotation"
        model = self._find_model_from_identity(identity)
        url_ref: str = ""
        for i in range(len(request.scope["headers"])):
            if len(request.scope["headers"][i]) > 1:
                for i1 in request.scope["headers"][i]:
                    if isinstance(i1, bytes):
                        val_i = i1.decode()
                    else:
                        val_i = i1
                    if val_i == "referer":
                        url_ref = request.scope["headers"][i][1]
        print(url_ref, "query_edit_quotation_details_url_reffffffffffff")
        if url_ref:
            query_update_quotation_details = dict(
                parse_qsl(urlsplit(str(url_ref)).query)
            )
            print(
                query_update_quotation_details,
                "query_edit_quotation_detailsssssssssssss",
            )
        print(request.method, "request_method_edit_quotation_detailssssssssssssssssss")

        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)

        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        query_edit_quotation = dict(parse_qsl(urlsplit(str(request.url)).query))
        print(query_edit_quotation, "query_edit_quotationeeeeeeeee")

        model11 = self._find_model_from_identity("quotationsdetails1_tbl")
        get_all_actions = await model11.get_all_actions(request)

        dict_obj: dict[str:str] = dict()

        with Session(
            engine[engine_nick[query_update_quotation_details["DBname"]]]
        ) as session:
            stmt_update_quotation_details = (
                update(QuotationsDetails_tbl)
                .values(
                    Qty=query_edit_quotation["Qty"],
                    UnitPrice=query_edit_quotation["UnitPrice"],
                )
                .where(
                    QuotationsDetails_tbl.LineID
                    == query_update_quotation_details["LineID"]
                )
            )
            print(
                stmt_update_quotation_details,
                "stmt_update_items_alchemyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
            )
            answ_update_quotation_details = session.execute(
                stmt_update_quotation_details
            )
            session.commit()

            stmt_quotation_edit_sum = select(
                QuotationsDetails_tbl.UnitPrice,
                QuotationsDetails_tbl.Qty,
            ).where(
                QuotationsDetails_tbl.QuotationID
                == query_update_quotation_details["QuotationID"],
            )

            rows_quotation_edit_sum = (
                session.execute(stmt_quotation_edit_sum).mappings().all()
            )

            print(
                rows_quotation_edit_sum,
                len(rows_quotation_edit_sum),
                "rows_quotation_edit_summmmmmmmmm",
            )
            total_sum: list[str] = list()
            for i in rows_quotation_edit_sum:
                total_sum.append(float(i["UnitPrice"]) * float(i["Qty"]))

            print(total_sum, len(total_sum), sum(total_sum), "total_summmmmmmmmmmm")

            stmt_update_quotation_sum = (
                update(Quotations_tbl)
                .values(
                    QuotationTotal=sum(total_sum),
                )
                .where(
                    Quotations_tbl.QuotationID
                    == query_update_quotation_details["QuotationID"]
                )
            )
            print(
                stmt_update_quotation_sum,
                "stmt_update_quotation_summmmmmmmmmmm",
            )
            answ_update_quotation_details = session.execute(stmt_update_quotation_sum)
            session.commit()

            stmt_quotation_edit = (
                select(
                    Quotations_tbl.__table__.columns,
                    QuotationsDetails_tbl.LineID.label("QuotationsDetails_id"),
                    QuotationsDetails_tbl.ProductDescription.label(
                        "QuotationsDetails_ProductDescription"
                    ),
                    QuotationsDetails_tbl.ProductSKU.label(
                        "QuotationsDetails_ProductSKU"
                    ),
                )
                .join(
                    QuotationsDetails_tbl,
                    Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                )
                .where(
                    and_(
                        QuotationsDetails_tbl.QuotationID
                        == query_update_quotation_details["QuotationID"],
                        QuotationsDetails_tbl.LineID
                        == query_update_quotation_details["LineID"],
                    )
                )
            )

            rows_quotation_edit = session.execute(stmt_quotation_edit).mappings().all()

            print(
                rows_quotation_edit,
                len(rows_quotation_edit),
                "rows_quotation_editttttttttttt",
            )
            dict_obj.update({"SourceDB": query_update_quotation_details["DBname"]})
            dict_obj.update(
                {"QuotationNumber": rows_quotation_edit[0]["QuotationNumber"]}
            )
            dict_obj.update({"BusinessName": rows_quotation_edit[0]["BusinessName"]})
            dict_obj.update({"AccountNo": rows_quotation_edit[0]["AccountNo"]})
            dict_obj.update(
                {"QuotationID": query_update_quotation_details["QuotationID"]}
            )
            dict_obj.update(
                {"Total": f"${round(rows_quotation_edit[0]['QuotationTotal'], 2)}"}
            )
            dict_obj.update({"Total Items": f"{len(rows_quotation_edit_sum)}"})

        successfully = f"Item {rows_quotation_edit[0]['QuotationsDetails_ProductDescription']} successfully update"
        return_list = "ok"

        return self.templates.TemplateResponse(
            "edit_quotation.html",
            {
                "request": request,
                "model": model,
                "return_list": return_list,
                "update": successfully,
                "obj": dict_obj,
                "menu": menu(request),
            },
        )

    async def update_quotation_details(self, request: Request) -> Response:
        print(
            "PRESS_BUTTON__update_quotation_details_OKOKOKOK--------------------------------------------------------------------------"
        )
        print(request.__dict__, "requestttttttttttttttttttttt_update_quotation")
        dict_obj: dict[str:str] = dict()
        quotationdetails_dest_dict: Dict[int, int] = {}
        quotationdetails_dest_error_dict: Dict[int, int] = {}
        quotationdetails_dest_error_list = []
        successfully = ""
        answ_quotation_items_dict = {}
        identity = request.path_params.get("identity")
        identity1 = "update_quotation_details"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)

        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")
        query_update_quotation = dict(parse_qsl(urlsplit(str(request.url)).query))
        print(query_update_quotation, "_update_quotation_detailseeeeeeeee")

        model11 = self._find_model_from_identity("quotationsdetails1_tbl")
        get_all_actions = await model11.get_all_actions(request)
        config_model = await model11._configs(request)
        print(
            config_model,
            "config_modelllll_update_quotation_details----------===========>>>",
        )
        print(
            model.create_template,
            "model_create_templateeee_update_quotation_detailssssss",
        )
        url_ref: str = ""
        for i in range(len(request.scope["headers"])):
            if len(request.scope["headers"][i]) > 1:
                for i1 in request.scope["headers"][i]:
                    if isinstance(i1, bytes):
                        val_i = i1.decode()
                    else:
                        val_i = i1
                    if val_i == "referer":
                        url_ref = request.scope["headers"][i][1]
        print(url_ref, "query_update_quotation_details_url_reffffffffffff")
        if url_ref:
            query_update_quotation_details = dict(
                parse_qsl(urlsplit(str(url_ref)).query)
            )
            print(
                query_update_quotation_details,
                "query_update_quotation_detailsssssssssssss",
            )
        print(
            request.method, "request_method_update_quotation_detailssssssssssssssssss"
        )

        with Session(engine[engine_nick[query_update_quotation["DBname"]]]) as session:

            stmt_quotation_edit_count = select(
                func.count(QuotationsDetails_tbl.LineID).label(
                    "QuotationsDetails_count"
                ),
            ).filter_by(QuotationID=query_update_quotation["QuotationID"])
            rows_quotation_edit_count = (
                session.execute(stmt_quotation_edit_count).mappings().all()
            )
            print(rows_quotation_edit_count, "rows_quotation_edit_counttttttttt")

            stmt_quotation_edit = (
                select(
                    Quotations_tbl.__table__.columns,
                    QuotationsDetails_tbl.LineID.label("QuotationsDetails_id"),
                    QuotationsDetails_tbl.ProductDescription.label(
                        "QuotationsDetails_ProductDescription"
                    ),
                    QuotationsDetails_tbl.ProductSKU.label(
                        "QuotationsDetails_ProductSKU"
                    ),
                )
                .join(
                    QuotationsDetails_tbl,
                    Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                )
                .where(
                    and_(
                        QuotationsDetails_tbl.QuotationID
                        == query_update_quotation["QuotationID"],
                        QuotationsDetails_tbl.LineID
                        == query_update_quotation["LineID"],
                    )
                )
            )

            rows_quotation_edit = session.execute(stmt_quotation_edit).mappings().all()

            print(
                rows_quotation_edit,
                len(rows_quotation_edit),
                "rows_quotation_editttttttttttt",
            )

            dict_obj.update({"SourceDB": query_update_quotation["DBname"]})
            dict_obj.update(
                {"QuotationNumber": rows_quotation_edit[0]["QuotationNumber"]}
            )
            dict_obj.update({"BusinessName": rows_quotation_edit[0]["BusinessName"]})
            dict_obj.update({"AccountNo": rows_quotation_edit[0]["AccountNo"]})
            dict_obj.update(
                {"QuotationID": query_update_quotation_details["QuotationID"]}
            )

            dict_obj.update(
                {"Total": f"${round(rows_quotation_edit[0]['QuotationTotal'], 2)}"}
            )
            dict_obj.update(
                {
                    "Total Items": f"{rows_quotation_edit_count[0]['QuotationsDetails_count']}"
                }
            )

        obj_edit = {
            "Qty": query_update_quotation["Qty"],
            "UnitPrice": f'${query_update_quotation["UnitPrice"]}',
            "LineID": query_update_quotation["LineID"],
            "QuotationsDetails_ProductDescription": rows_quotation_edit[0][
                "QuotationsDetails_ProductDescription"
            ],
            "QuotationsDetails_ProductSKU": rows_quotation_edit[0][
                "QuotationsDetails_ProductSKU"
            ],
        }
        return self.templates.TemplateResponse(
            "edit_quotation.html",
            {
                "request": request,
                "model": model,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "obj_edit": obj_edit,
                "obj": dict_obj,
                "menu": menu(request),
            },
        )

    async def quotation_return(self, request: Request) -> Response:
        print(
            "quotation_return_eeeeeeeeeeeeeeeeeeeeeeeeeee----------------------------------------------------------------------------------------------------------------------------------"
        )
        identity = request.path_params.get("identity")
        identity1 = "quotation_return"
        model = self._find_model_from_identity(identity)
        get_all_actions = await model.get_all_actions(request)
        print(get_all_actions, "get_all_actionsssssssss----======>>>>")
        config_model = await model._configs(request)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)

        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")

        print(request.url, "request.urlllllllllll-----")

        url_params_dict = dict(parse_qsl(urlsplit(str(request.url)).query))
        print(url_params_dict, "url_params_dictlllllllllll-----")

        if "QuotationNumber" in url_params_dict:
            quotation_number = url_params_dict["QuotationNumber"]
        else:
            quotation_number = ""

        cancel_InvoiceNumber = url_params_dict["InvoiceNumber"]

        with Session(engine["DB1"]) as session:
            with Session(engine["DB_admin"]) as session1:
                stmt_quotation_status_temp = select(
                    Quotation.__table__.columns
                ).filter_by(InvoiceNumber=cancel_InvoiceNumber)

                rows_quotation_status_temp = (
                    session1.execute(stmt_quotation_status_temp).mappings().all()
                )

                rows_quotation_status = rows_quotation_status_temp[0]["Status"]
                print(
                    rows_quotation_status,
                    "rows_quotation_status_alchemyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
                )

                if rows_quotation_status == "VOIDED":
                    return self.templates.TemplateResponse(
                        "create_quotation.html",
                        {
                            "request": request,
                            "_actions": get_all_actions,
                            "__js_model__": config_model,
                            "model": self._find_model_from_identity("quotations_tbl"),
                            "update_error": f"Invoice: {cancel_InvoiceNumber} already canceled",
                            "menu": menu(request),
                        },
                    )

                query_cancel = f"select ProductUPC, (sum(qty)*-1) AS QTY from QuotationDetails where InvoiceNumber = '{cancel_InvoiceNumber}' group by ProductUPC"

                answ_cancel = pd_req(query_cancel, "DB_admin")
                print(
                    answ_cancel,
                    len(answ_cancel),
                    "answ_cancelllllllllllllll----------------------------",
                )

                for i in answ_cancel:
                    ProductUPC = i["ProductUPC"]
                    QTY_admin = i["QTY"]

                    stmt_quotation_check = select(
                        Items_tbl.__table__.columns
                    ).filter_by(ProductUPC=i["ProductUPC"])
                    rows_stmt_quotation_check = (
                        session.execute(stmt_quotation_check).mappings().all()
                    )
                    print(
                        rows_stmt_quotation_check,
                        "rows_stmt_quotation_check_alchemyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
                    )
                    QTY_items = rows_stmt_quotation_check[0]["QuantOnHand"]
                    ProductDescription = rows_stmt_quotation_check[0][
                        "ProductDescription"
                    ]
                    ProductSKU = rows_stmt_quotation_check[0]["ProductSKU"]
                    ProductUPC = rows_stmt_quotation_check[0]["ProductUPC"]
                    QTY_final = QTY_admin + QTY_items
                    print(
                        QTY_admin,
                        QTY_items,
                        QTY_final,
                        "QTY_adminnnnnnnnnnnnnnnnnnnnn---------------",
                    )

                    if QTY_admin != 0:
                        if cancel_InvoiceNumber and cancel_InvoiceNumber != None:
                            stmt_admin = insert(QuotationDetails).values(
                                QuotationNumber=quotation_number,
                                ProductDescription=ProductDescription,
                                ProductSKU=ProductSKU,
                                ProductUPC=ProductUPC,
                                QTY=QTY_admin,
                                InvoiceNumber=cancel_InvoiceNumber,
                                FlagOrder=True,
                            )
                        else:
                            stmt_admin = insert(QuotationDetails).values(
                                QuotationNumber=quotation_number,
                                ProductDescription=ProductDescription,
                                ProductSKU=ProductSKU,
                                ProductUPC=ProductUPC,
                                QTY=QTY_admin,
                                FlagOrder=False,
                            )
                        rows_admin = session1.execute(stmt_admin).mappings().all()
                        print(rows_admin, "rows_alchemyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")

                        stmt_update_items = (
                            update(Items_tbl)
                            .values(QuantOnHand=QTY_final)
                            .where(Items_tbl.ProductUPC == ProductUPC)
                        )
                        print(
                            stmt_update_items,
                            "stmt_update_items_alchemyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
                        )
                        answ_update_items = session.execute(stmt_update_items)
                session.commit()

                stmt_status = (
                    update(Quotation)
                    .values(Status="VOIDED", LastUpdate=time_now_5h)
                    .where(Quotation.InvoiceNumber == cancel_InvoiceNumber)
                )
                print(stmt_status, "stmtpppp_fdggalchemyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")
                rows = session1.execute(stmt_status)

                session1.commit()

        with Session(engine["DB_admin"]) as session2:

            stmt_quotation_SourceDB = select(Quotation.SourceDB).filter_by(
                InvoiceNumber=cancel_InvoiceNumber
            )
            rows_quotation_SourceDB = (
                session2.execute(stmt_quotation_SourceDB).mappings().all()
            )

        SourceDB = rows_quotation_SourceDB[0]["SourceDB"]

        with Session(engine[engine_nick[SourceDB]]) as session3:

            stmt_update_void = (
                update(Invoices_tbl)
                .values(
                    Void=True,
                    InvoiceType="WM",
                )
                .where(Invoices_tbl.InvoiceNumber == cancel_InvoiceNumber)
                .returning(
                    Invoices_tbl.InvoiceID,
                )
            )
            answ_update_void = session3.execute(stmt_update_void).mappings().all()
            InvoiceID = answ_update_void[0]["InvoiceID"]

            stmt_update_details_void = (
                update(InvoicesDetails_tbl)
                .values(Void=True)
                .where(InvoicesDetails_tbl.InvoiceID == InvoiceID)
            )
            answ_update_details_void = session3.execute(stmt_update_details_void)
            session3.commit()

        return self.templates.TemplateResponse(
            "create_quotation.html",
            {
                "request": request,
                "_actions": get_all_actions,
                "__js_model__": config_model,
                "model": self._find_model_from_identity("quotations_tbl"),
                "update": f"Invoice: {cancel_InvoiceNumber} Successfully Return",
                "menu": menu(request),
            },
        )

    async def users(self, request: Request) -> Response:
        if check_token(request) == False:
            return JSONResponse({"ERROR": "Wrong Token"})
        dict_answ = {
            "data_allusers": {
                "data": [],
                "status": "ok",
                "error": 0,
                "error_info": "",
            }
        }

        with Session(engine["DB_admin"]) as session:
            query_all_userd = select(AdminUserProject_admin.__table__.columns)
            answ_all_users = session.execute(query_all_userd).mappings().all()
            if answ_all_users:
                [
                    dict_answ["data_allusers"]["data"].append(dict(i))
                    for i in answ_all_users
                ]

        return JSONResponse(dict_answ)

    async def checkactivequotations(self, request: Request) -> Response:
        if check_token(request) == False:
            return JSONResponse({"ERROR": "Wrong Token"})
        dict_answ = {
            "data_checkactivequotations": {
                "data": [],
                "status": "ok",
                "error": 0,
                "error_info": "",
            }
        }

        with Session(engine["DB_admin"]) as session:
            query_checkactivequotations = select(QuotationsInProgress.__table__.columns)
            answ_checkactivequotations = (
                session.execute(query_checkactivequotations).mappings().all()
            )
            if answ_checkactivequotations:
                for i in answ_checkactivequotations:
                    i = dict(i)
                    for i_dict in i:
                        if isinstance(i[i_dict], datetime.datetime):
                            i[i_dict] = i[i_dict].strftime("%Y-%m-%d %H:%M:%S")
                    dict_answ["data_checkactivequotations"]["data"].append(dict(i))
        return JSONResponse(dict_answ)

    async def checkprogress(self, request: Request) -> Response:
        if check_token(request) == False:
            return JSONResponse({"ERROR": "Wrong Token"})
        form = await request.form()
        dict_form = dict(form)
        QuotationNumber = dict_form["Quotationnumber"]
        user_status = dict_form["status"]
        if user_status == "packer":
            Packer = "packer"
        elif user_status == "checker":
            Checker = "checker"
        user_name = dict_form["user_name"]
        SourceDB = dict_form["SourceDB"]
        status = ""
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")

        with Session(engine[SourceDB]) as session:
            query_Quotation = (
                select(
                    Quotations_tbl.__table__.columns,
                    QuotationsDetails_tbl.__table__.columns,
                )
                .join(
                    QuotationsDetails_tbl,
                    Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                )
                .where(Quotations_tbl.QuotationNumber == QuotationNumber)
            )

            answ_Quotation = session.execute(query_Quotation).mappings().all()

        with Session(engine["DB_admin"]) as session:
            query_checkactivequotations = select(
                QuotationsInProgress.__table__.columns
            ).filter_by(QuotationNumber=QuotationNumber)
            answ_checkactivequotations = (
                session.execute(query_checkactivequotations).mappings().all()
            )

        dict_answ = {
            "data_check_progress": {
                "data": [],
                "status": status,
                "error": 0,
                "error_info": "",
            }
        }

        return JSONResponse(dict_answ)

    async def items_all(self, request: Request) -> Response:
        print("items_alleeeeeee-------------------------------------")

        if check_token(request) == False:
            return JSONResponse({"ERROR": "Wrong Token"})

        form = await request.form()
        dict_form = dict(form)
        print(dict_form, "form_items_alleeeeeeeeeo")
        SourceDB = dict_form["SourceDB"]
        time_now_5h = (
            datetime.datetime.today() - datetime.timedelta(hours=5)
        ).strftime("%Y-%m-%d %H:%M:%S")

        with Session(engine[SourceDB]) as session:
            query_items_all = select(
                Items_tbl.ProductID,
                Items_tbl.ProductDescription,
                Items_tbl.ProductSKU,
                Items_tbl.ProductUPC,
            )
            answ_items_all = session.execute(query_items_all).mappings().all()
        answ_items_all_temp = [dict(i) for i in answ_items_all]
        dict_answ = {
            "data_items_all": {
                "data": answ_items_all_temp,
                "error": 0,
                "error_info": "",
            }
        }
        return JSONResponse(dict_answ)

    async def wl1(self, request: Request) -> Response:
        if check_token(request) == False:
            return JSONResponse({"ERROR": "Wrong Token"})
        form = await request.form()
        file = form["file"]
        contents = await file.read()
        with open(abs_path(data="cq"), "a") as f:
            f.write(contents.decode("utf-8"))
        return JSONResponse({"status": "ok"})

    async def wl2(self, request: Request) -> Response:
        if check_token(request) == False:
            return JSONResponse({"ERROR": "Wrong Token"})
        form = await request.form()
        file = form["file"]
        contents = await file.read()
        with open(abs_path(data="cm"), "a") as f:
            f.write(contents.decode("utf-8"))
        return JSONResponse({"status": "ok"})

    async def SourceDB(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "SourceDB"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        items = await model.find_all_choicedb_source(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        if len(items) == 1:
            flag = 0
        else:
            flag = 1

        for item in items:
            res_dict_temp = {}
            alias = engine_nick[item["Nick"]]
            query_alias = f'{item["Nick"]}'
            res_dict_temp.update(
                {
                    "id": alias,
                    "SourceDB": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)
            res_dict.update({"error": 0})
            res_dict.update({"error_info": ""})

        response = JSONResponse(res_dict)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def SourceDBcopy(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        identity1 = "SourceDBcopy"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        res_dict = {"items": []}
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        items = await model.find_all_choicedb_source(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
        )
        print(items, engine_nick, "itemssss__SourceDBcopy------------------")
        if len(items) == 1:
            flag = 0
        else:
            flag = 1

        for item in items:
            res_dict_temp = {}
            alias = engine_nick[item["Nick"]]
            query_alias = f'{item["Nick"]}'
            res_dict_temp.update(
                {
                    "id": query_alias,
                    "SourceDBcopy": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)
        return JSONResponse(res_dict)

    async def businessnamequotation(self, request: Request) -> Response:
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        res_dict = {"items": []}
        query_string_dict = dict(parse_qsl(query_string))
        source_db_form = ""
        if "dop" in query_string_dict:
            query_string_dict_dop = query_string_dict["dop"]
            source_db_form = query_string_dict["dop"]
        else:
            return JSONResponse(res_dict)

        identity = request.path_params.get("identity")
        identity1 = "businessnamequotation"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        form = await request.form()

        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        obj = await model.add_items_quotation(request, dict_obj)
        items = await model.find_all_businessnamequotation(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
            dict_obj=dict_obj,
            model=model,
            db_form=source_db_form,
        )

        if len(items) == 1:
            flag = 0
        else:
            flag = 1

        for item in items:
            res_dict_temp = {}

            alias = f'{item["CustomerID"]}'
            query_alias = f'{item["BusinessName"]}'
            res_dict_temp.update(
                {
                    "id": query_alias,
                    "businessnamequotation": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)

        return JSONResponse(res_dict)

    async def accountnoquotation(self, request: Request) -> Response:
        print("accountnoquotation_eeeeeeeeeeeeeeeeeeeeeeeeeee-----------------------")
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        print(query_string, "query_stringggggggggggggggggggg")
        res_dict = {"items": []}
        query_string_dict = dict(parse_qsl(query_string))
        print(query_string_dict, "query_string_dicttttttttttt")

        source_db_form = ""

        if "dop" in query_string_dict:
            query_string_dict_dop = query_string_dict["dop"]
            print(
                query_string_dict_dop,
                type(query_string_dict_dop),
                "accountnoquotation_query_stringggggggggg",
            )
            source_db_form = query_string_dict["dop"]
        else:
            return JSONResponse(res_dict)

        identity = request.path_params.get("identity")
        identity1 = "accountnoquotation"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params

        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        items = await model.find_all_accountnoquotation(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
            db_form=source_db_form,
        )
        res_dict = {"items": []}

        if len(items) == 1:
            flag = 0
        else:
            flag = 1

        for item in items:
            print(item, "----accountnoquotation")
            res_dict_temp = {}
            alias = f'{item["CustomerID"]}'
            query_alias = f'{item["AccountNo"]}'
            res_dict_temp.update(
                {
                    "id": query_alias,
                    "accountnoquotation": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)

        return JSONResponse(res_dict)

    async def productdescriptionquotation(self, request: Request) -> Response:
        print("productdescriptionquotation_eeeeeeeeeeeeeeeeeeeeeeeeeee------------")
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        print(query_string, "query_stringggggggggggggggggggg")
        res_dict = {"items": []}
        query_string_dict = dict(parse_qsl(query_string))
        print(query_string_dict, "query_string_dicttttttttttt")
        source_db_form = ""

        if "dop" in query_string_dict:
            query_string_dict_dop = query_string_dict["dop"]
            print(
                query_string_dict_dop,
                type(query_string_dict_dop),
                "productdescriptionquotation_query_stringggggggggg",
            )
            source_db_form = query_string_dict["dop"]
        else:
            print("NO_doppppppppppppppppppppppp----")
            return JSONResponse(res_dict)

        identity = request.path_params.get("identity")
        print(identity, "identityyyyyyyyy")
        identity1 = "productdescriptionquotation"
        model = self._find_model_from_identity(identity)
        print(model.__dict__, "modelllllllllllllllllll")
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        print(dict_obj, "dict_obj__add_items_quotationnnnnnnnnnnnnnnnnnn")
        obj = await model.add_items_quotation(request, dict_obj)
        print(obj, "obj__add_items_quotationnnnnnnnnnnnnnnnnnn")

        items = await model.find_all_productdescriptionquotation(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
            dict_obj=dict_obj,
            model=model,
            db_form=source_db_form,
        )

        if len(items) == 1:
            flag = 0
        else:
            flag = 1

        for item in items:
            res_dict_temp = {}
            alias = f'{item["ProductID"]}'
            query_alias = f'{item["ProductDescription"]}'
            res_dict_temp.update(
                {
                    "id": query_alias,
                    "productdescriptionquotation": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)

        return JSONResponse(res_dict)

    async def productskuquotation(self, request: Request) -> Response:
        print("productskuquotation_eeeeeeeeeeeeeeeeeeeeeeeeeee------------")
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        print(query_string, "query_stringggggggggggggggggggg")
        res_dict = {"items": []}
        query_string_dict = dict(parse_qsl(query_string))
        print(query_string_dict, "query_string_dicttttttttttt")

        source_db_form = ""

        if "dop" in query_string_dict:
            query_string_dict_dop = query_string_dict["dop"]
            print(
                query_string_dict_dop,
                type(query_string_dict_dop),
                "productskuquotation_query_stringggggggggg",
            )
            source_db_form = query_string_dict["dop"]
        else:
            print("NO_doppppppppppppppppppppppp----")
            return JSONResponse(res_dict)

        identity = request.path_params.get("identity")
        identity1 = "productskuquotation"
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        print(dict_obj, "dict_obj__add_items_quotationnnnnnnnnnnnnnnnnnn")
        obj = await model.add_items_quotation(request, dict_obj)
        print(obj, "obj__add_items_quotationnnnnnnnnnnnnnnnnnn")

        items = await model.find_all_productskuquotation(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
            dict_obj=dict_obj,
            model=model,
            db_form=source_db_form,
        )

        if len(items) == 1:
            flag = 0
        else:
            flag = 1

        for item in items:
            res_dict_temp = {}
            alias = f'{item["ProductID"]}'
            query_alias = f'{item["ProductSKU"]}'
            res_dict_temp.update(
                {
                    "id": query_alias,
                    "productskuquotation": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)

        print(JSONResponse(res_dict).__dict__, "JSONResponseeeeeeeeeeeee")
        return JSONResponse(res_dict)

    async def productdescriptionquotationedit(self, request: Request) -> Response:
        print("productdescriptionquotationedit_eeeeeeeeeeeeeeeeeeeeeeeeeee------------")
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        print(query_string, "query_stringggggggggggggggggggg")
        res_dict = {"items": []}
        query_string_dict = dict(parse_qsl(query_string))
        print(query_string_dict, "query_string_dicttttttttttt")
        source_db_form = ""

        if "dop" in query_string_dict:
            query_string_dict_dop = query_string_dict["dop"]
            print(
                query_string_dict_dop,
                type(query_string_dict_dop),
                "productdescriptionquotationedit_query_stringggggggggg",
            )
            source_db_form = query_string_dict["dop"]
        else:
            print("NO_doppppppppppppppppppppppp----")
            return JSONResponse(res_dict)

        identity1 = "productdescriptionquotationedit"

        model = self._find_model_from_identity("quotationsdetails1_tbl")
        get_all_actions = await model.get_all_actions(request)
        config_model = await model._configs(request)
        print(
            config_model,
            "config_modelllll_update_quotation_details----------===========>>>",
        )

        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        print(dict_obj, "dict_obj__add_items_quotationnnnnnnnnnnnnnnnnnn")
        obj = await model.add_items_quotation(request, dict_obj)
        print(obj, "obj__add_items_quotationnnnnnnnnnnnnnnnnnn")

        items = await model.find_all_productdescriptionquotationedit(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
            dict_obj=dict_obj,
            model=model,
            db_form=source_db_form,
        )

        if len(items) == 1:
            flag = 0
        else:
            flag = 1

        for item in items:
            print(item, "----find_all_productdescriptionquotationedit")

            res_dict_temp = {}
            alias = f'{item["ProductID"]}'
            query_alias_descr = f'{item["ProductDescription"]}'
            query_alias_sku = f'{item["ProductSKU"]}'

            res_dict_temp.update(
                {
                    "id": query_alias_sku,
                    "productdescriptionquotationedit": f"{query_alias_descr} --> {query_alias_sku}",
                    "productskuedit": query_alias_sku,
                    "_select2_selection": f"<span><strong>{query_alias_sku}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias_sku}</strong></span>",
                    "flag": flag,
                }
            )

            res_dict["items"].append(res_dict_temp)

        print(
            json.dumps(res_dict, ensure_ascii=False, indent=4), "res_dicttttttttttttt"
        )
        return JSONResponse(res_dict)

    async def productskuquotationedit(self, request: Request) -> Response:
        print("productskuquotationedit_eeeeeeeeeeeeeeeeeeeeeeeeeee------------")
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        print(query_string, "query_stringggggggggggggggggggg")
        res_dict = {"items": []}
        query_string_dict = dict(parse_qsl(query_string))
        print(query_string_dict, "query_string_dicttttttttttt")

        source_db_form = ""

        if "dop" in query_string_dict:
            query_string_dict_dop = query_string_dict["dop"]
            print(
                query_string_dict_dop,
                type(query_string_dict_dop),
                "productskuquotationedit_query_stringggggggggg",
            )
            source_db_form = query_string_dict["dop"]
        else:
            print("NO_doppppppppppppppppppppppp----")
            return JSONResponse(res_dict)

        identity = request.path_params.get("identity")
        identity1 = "productskuquotationedit"
        model = self._find_model_from_identity("quotationsdetails1_tbl")
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        name_table = model.__dict__["name"].replace(" ", "")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        if where == "undefined" or pks == "undefined":
            return JSONResponse(res_dict)

        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        print(dict_obj, "dict_obj__add_items_quotationnnnnnnnnnnnnnnnnnn")
        obj = await model.add_items_quotation(request, dict_obj)
        print(obj, "obj__add_items_quotationnnnnnnnnnnnnnnnnnn")

        items = await model.find_all_productskuquotation(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
            dict_obj=dict_obj,
            model=model,
            db_form=source_db_form,
        )

        if len(items) == 1:
            flag = 0
        else:
            flag = 1

        for item in items:
            res_dict_temp = {}
            alias = f'{item["ProductID"]}'
            query_alias = f'{item["ProductSKU"]}'
            res_dict_temp.update(
                {
                    "id": query_alias,
                    "productskuquotationedit": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                }
            )
            res_dict["items"].append(res_dict_temp)

        print(JSONResponse(res_dict).__dict__, "JSONResponseeeeeeeeeeeee")
        return JSONResponse(res_dict)

    async def productdescriptionmanual(self, request: Request) -> Response:
        print("productdescriptionmanual_eeeeeeeeeeeeeeeeeeeeeeeeeee------------")
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        print(query_string, "query_stringggggggggggggggggggg")
        res_dict = {"items": []}
        query_string_dict = dict(parse_qsl(query_string))
        print(query_string_dict, "productdescriptionmanual_query_string_dicttttttttttt")

        source_db_form = ""

        identity1 = "productdescriptionmanual"
        print(identity1, "identity1_manuallll")

        model = self._find_model_from_identity("manualinventoryupdate")
        print(model, "model_manuallllllll")

        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params

        form = await request.form()
        print(form, "formmmm--------------------------<<<<<")
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        print(dict_obj, "dict_obj__add_items_quotationnnnnnnnnnnnnnnnnnn")

        items = await model.find_all_productdescriptionmanual(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
            dict_obj=dict_obj,
            model=model,
            db_form=source_db_form,
        )

        if len(items) == 1:
            flag = 0
        elif len(items) > 1:
            if items[0]["ProductDescription"] == items[1]["ProductDescription"]:
                flag = 0
            else:
                flag = 1

        for item in items:
            res_dict_temp = {}
            alias = f'{item["ProductID"]}'
            query_alias = f'{item["ProductDescription"]}'
            res_dict_temp.update(
                {
                    "id": query_alias,
                    "productdescriptionmanual": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                    "item_id": item["ProductID"],
                }
            )
            res_dict["items"].append(res_dict_temp)

        return JSONResponse(res_dict)

    async def productskumanual(self, request: Request) -> Response:
        print("productskumanual_eeeeeeeeeeeeeeeeeeeeeeeeeee------------")
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        print(query_string, "query_stringggggggggggggggggggg")
        res_dict = {"items": []}
        query_string_dict = dict(parse_qsl(query_string))
        print(query_string_dict, "query_string_dicttttttttttt")

        source_db_form = ""

        identity1 = "productskumanual"

        model = self._find_model_from_identity("manualinventoryupdate")
        print(model, "model_manuallllllll")

        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params

        form = await request.form()
        print(form, "formmmm--------------------------<<<<<")
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        print(dict_obj, "dict_obj__add_items_quotationnnnnnnnnnnnnnnnnnn")

        items = await model.find_all_productskumanual(
            request=request,
            skip=skip,
            limit=limit,
            where=where,
            order_by=order_by,
            other=identity1,
            dict_obj=dict_obj,
            model=model,
            db_form=source_db_form,
        )

        if len(items) == 1:
            flag = 0
        elif len(items) > 1:
            if items[0]["ProductSKU"] == items[1]["ProductSKU"]:
                flag = 0
            else:
                flag = 1

        for item in items:
            res_dict_temp = {}
            alias = f'{item["ProductID"]}'
            query_alias = f'{item["ProductSKU"]}'
            res_dict_temp.update(
                {
                    "id": query_alias,
                    "productskumanual": query_alias,
                    "_select2_selection": f"<span><strong>{query_alias}</strong></span>",
                    "_select2_result": f"<span><strong>{query_alias}</strong></span>",
                    "flag": flag,
                    "item_id": item["ProductID"],
                }
            )
            res_dict["items"].append(res_dict_temp)

        return JSONResponse(res_dict)

    async def browseitems(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            AccountNo = dict_form["anum"]
            if not AccountNo and "ignoreaccout" not in dict_form:
                dict_answ = {
                    "data": [],
                    "error": 1,
                    "error_info": "AccountNo not present",
                }
                response = JSONResponse(dict_answ)
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            with Session(engine[dict_form["DB"]]) as session:
                searchById = dict_form["searchById"]
                where = dict_form["searchValue"]
                stmt_checkbrowseitems = select(
                    Items_tbl.ProductUPC,
                    Items_tbl.ProductDescription,
                    Items_tbl.UnitPrice,
                    Items_tbl.UnitCost,
                    Items_tbl.ProductSKU,
                    Items_tbl.ExpDate,
                ).limit(1000)

                if searchById == "1":
                    stmt_checkbrowseitems = stmt_checkbrowseitems.where(
                        and_(
                            Items_tbl.Discontinued == 0,
                            Items_tbl.ProductSKU.like(f"{where}%"),
                        )
                    )
                elif searchById == "2":
                    stmt_checkbrowseitems = stmt_checkbrowseitems.where(
                        and_(
                            Items_tbl.Discontinued == 0,
                            Items_tbl.ProductUPC.like(f"{where}%"),
                        )
                    )
                elif searchById == "3":
                    stmt_checkbrowseitems = stmt_checkbrowseitems.where(
                        and_(
                            Items_tbl.Discontinued == 0,
                            Items_tbl.ProductDescription.like(f"{where}%"),
                        )
                    )

                stmt_checkbrowseitems = stmt_checkbrowseitems.order_by(
                    Items_tbl.ProductDescription.asc()
                )

                rows_checkbrowseitems = (
                    session.execute(stmt_checkbrowseitems).mappings().all()
                )

            if rows_checkbrowseitems:
                upc_list = [i["ProductUPC"] for i in rows_checkbrowseitems if i["ProductUPC"]]
                rememberprice_map = {}
                unitprice_map = {}

                if upc_list:
                    with Session(engine[dict_form["DB"]]) as session:
                        stmt_check_mem = (
                            select(
                                InvoicesDetails_tbl.ProductUPC,
                                Invoices_tbl.InvoiceDate,
                                InvoicesDetails_tbl.UnitPrice,
                            )
                            .join(
                                Invoices_tbl,
                                Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID,
                            )
                            .where(
                                and_(
                                    Invoices_tbl.Void == 0,
                                    Invoices_tbl.InvoiceTitle.notin_(ch_lis),
                                    Invoices_tbl.AccountNo == AccountNo,
                                    InvoicesDetails_tbl.ProductUPC.in_(upc_list),
                                    InvoicesDetails_tbl.RememberPrice == 1,
                                )
                            )
                            .order_by(Invoices_tbl.InvoiceNumber.desc())
                        )
                        rows_check_mem = session.execute(stmt_check_mem).mappings().all()
                        for row in rows_check_mem:
                            upc = row["ProductUPC"]
                            if upc not in rememberprice_map:
                                rememberprice_map[upc] = row["InvoiceDate"]
                                unitprice_map[upc] = row["UnitPrice"]

                for i in rows_checkbrowseitems:
                    dict_answ_temp = dict()
                    ProductUPC = i["ProductUPC"]
                    ProductDescription = i["ProductDescription"]
                    UnitPrice = i["UnitPrice"]
                    UnitCost = i["UnitCost"]
                    ProductSKU = i["ProductSKU"]
                    ExpDate_items = i["ExpDate"]
                    if UnitCost is None:
                        UnitCost = 0
                    if UnitPrice is None:
                        UnitPrice = 0

                    rememberprice = 0
                    if ProductUPC in rememberprice_map:
                        InvoiceDate = rememberprice_map[ProductUPC]
                        if ExpDate_items is not None:
                            if InvoiceDate <= ExpDate_items:
                                rememberprice = 0
                            else:
                                UnitPrice = unitprice_map[ProductUPC]
                                rememberprice = 1
                        else:
                            rememberprice = 1
                            UnitPrice = unitprice_map[ProductUPC]
                    else:
                        rememberprice = 0

                    dict_answ_temp["UPC"] = ProductUPC
                    dict_answ_temp["Description"] = ProductDescription
                    dict_answ_temp["UnitPrice"] = float(UnitPrice)
                    dict_answ_temp["UnitCost"] = float(UnitCost)
                    dict_answ_temp["SKU"] = ProductSKU
                    dict_answ_temp["rememberprice"] = rememberprice
                    dict_answ_temp["Stock"] = 0
                    dict_answ["data"].append(dict_answ_temp)
                    dict_answ.update(
                        {
                            "error": 0,
                            "error_info": "",
                        }
                    )
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def browseitemsone(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            AccountNo = dict_form["anum"]
            with Session(engine[dict_form["DB"]]) as session:
                searchById = dict_form["searchById"]
                where = dict_form["searchValue"]
                stmt_checkbrowseitemsone = select(
                    Items_tbl.ProductUPC,
                    Items_tbl.ProductDescription,
                    Items_tbl.UnitPrice,
                    Items_tbl.UnitCost,
                    Items_tbl.ProductSKU,
                )
                if searchById == "1":
                    stmt_checkbrowseitemsone = stmt_checkbrowseitemsone.where(
                        and_(
                            Items_tbl.ProductSKU == where,
                        )
                    )
                elif searchById == "2":
                    stmt_checkbrowseitemsone = stmt_checkbrowseitemsone.where(
                        and_(
                            Items_tbl.ProductUPC == where,
                        )
                    )
                rows_checkbrowseitemsone = (
                    session.execute(stmt_checkbrowseitemsone).mappings().all()
                )
            if rows_checkbrowseitemsone:
                with Session(engine["DB1"]) as session1:
                    with Session(engine[dict_form["DB"]]) as session:
                        for i in rows_checkbrowseitemsone:
                            dict_answ_temp = dict()
                            ProductUPC = i["ProductUPC"]
                            ProductDescription = i["ProductDescription"]
                            UnitPrice = i["UnitPrice"]
                            UnitCost = i["UnitCost"]
                            ProductSKU = i["ProductSKU"]
                            stmt_check_mem = (
                                select(
                                    Invoices_tbl.InvoiceNumber,
                                    Invoices_tbl.InvoiceDate,
                                    InvoicesDetails_tbl.UnitPrice,
                                    InvoicesDetails_tbl.ProductUPC,
                                )
                                .join(
                                    Invoices_tbl,
                                    Invoices_tbl.InvoiceID
                                    == InvoicesDetails_tbl.InvoiceID,
                                )
                                .where(
                                    and_(
                                        Invoices_tbl.AccountNo == AccountNo,
                                        InvoicesDetails_tbl.ProductUPC == ProductUPC,
                                    )
                                )
                                .order_by(Invoices_tbl.InvoiceNumber.desc())
                            )

                            rows_check_mem = (
                                session.execute(stmt_check_mem).mappings().all()
                            )

                            if rows_check_mem:
                                InvoiceDate = rows_check_mem[0]["InvoiceDate"].strftime(
                                    "%Y-%m-%d"
                                )
                                InvoiceDate = datetime.datetime.strptime(
                                    InvoiceDate, "%Y-%m-%d"
                                )
                                stmt_check_mem_items = select(
                                    Items_tbl.UnitPrice,
                                    Items_tbl.ExpDate,
                                ).filter_by(ProductUPC=ProductUPC)
                                rows_check_mem_items = (
                                    session1.execute(stmt_check_mem_items)
                                    .mappings()
                                    .all()
                                )
                                ExpDate_items = rows_check_mem_items[0]["ExpDate"]

                                if InvoiceDate <= ExpDate_items:
                                    rememberprice = 0
                                else:
                                    UnitPrice = rows_check_mem[0]["UnitPrice"]
                                    rememberprice = 1
                            else:
                                rememberprice = 0

                        dict_answ_temp["UPC"] = ProductUPC
                        dict_answ_temp["Description"] = ProductDescription
                        dict_answ_temp["UnitPrice"] = float(UnitPrice)
                        dict_answ_temp["UnitCost"] = float(UnitCost)
                        dict_answ_temp["SKU"] = ProductSKU

                        stmt_checkdb1 = select(
                            Items_tbl.QuantOnHand,
                        ).filter_by(ProductUPC=ProductUPC)
                        rows_checkdb1 = session1.execute(stmt_checkdb1).mappings().all()

                        if rows_checkdb1:
                            dict_answ_temp["Stock"] = int(
                                rows_checkdb1[0]["QuantOnHand"]
                            )

                        else:
                            dict_answ_temp["Stock"] = 0

                        dict_answ_temp["rememberprice"] = rememberprice

                        if "isStockRequested" in dict_answ:
                            if dict_answ["isStockRequested"] == 1:
                                stmt_checkdb1 = select(
                                    Items_tbl.QuantOnHand,
                                ).filter_by(ProductUPC=ProductUPC)
                                rows_checkdb1 = (
                                    session1.execute(stmt_checkdb1).mappings().all()
                                )
                                dict_answ_temp["Stock"] = int(
                                    rows_checkdb1[0]["QuantOnHand"]
                                )
                            elif dict_answ["isStockRequested"] == 0:
                                dict_answ_temp["Stock"] = 0

                        elif "isStockRequested" not in dict_answ:
                            stmt_checkdb1 = select(
                                Items_tbl.QuantOnHand,
                            ).filter_by(ProductUPC=ProductUPC)
                            rows_checkdb1 = (
                                session1.execute(stmt_checkdb1).mappings().all()
                            )
                            dict_answ_temp["Stock"] = int(
                                rows_checkdb1[0]["QuantOnHand"]
                            )

                        dict_answ["data"].append(dict_answ_temp)

            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def getitemsmassupdate(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            with Session(engine[dict_form["DB"]]) as session:
                searchById = dict_form["searchById"]
                where = dict_form["searchValue"]
                stmt_checkbrowseitems = select(
                    Items_tbl.ProductUPC,
                    Items_tbl.ProductDescription,
                    Items_tbl.UnitPrice,
                    Items_tbl.UnitCost,
                    Items_tbl.ProductSKU,
                    Items_tbl.Discontinued,
                    Items_tbl.UnitPriceC,
                    Items_tbl.ExpDate,
                )

                if searchById == "1":
                    stmt_checkbrowseitems = stmt_checkbrowseitems.where(
                        and_(
                            Items_tbl.ProductSKU.like(f"%{where}%"),
                        )
                    )
                elif searchById == "2":
                    stmt_checkbrowseitems = stmt_checkbrowseitems.where(
                        and_(
                            Items_tbl.ProductUPC.like(f"{where}%"),
                        )
                    )
                elif searchById == "3":
                    stmt_checkbrowseitems = stmt_checkbrowseitems.where(
                        and_(
                            Items_tbl.ProductDescription.like(f"%{where}%"),
                        )
                    )

                stmt_checkbrowseitems = stmt_checkbrowseitems.order_by(
                    Items_tbl.ProductDescription.desc()
                )

                rows_checkbrowseitems = (
                    session.execute(stmt_checkbrowseitems).mappings().all()
                )

            if rows_checkbrowseitems:
                for i in rows_checkbrowseitems:
                    dict_answ_temp = dict()
                    ProductUPC = i["ProductUPC"]
                    ProductDescription = i["ProductDescription"]
                    UnitPrice = i["UnitPrice"]
                    UnitCost = i["UnitCost"]
                    Discontinued = i["Discontinued"]
                    UnitPriceC = float(i["UnitPriceC"])
                    ExpDate = i["ExpDate"].strftime("%m-%d-%Y %H:%M")
                    ProductSKU = i["ProductSKU"]
                    dict_answ_temp["UPC"] = ProductUPC
                    dict_answ_temp["Description"] = ProductDescription
                    dict_answ_temp["UnitPrice"] = float(UnitPrice)
                    dict_answ_temp["UnitCost"] = float(UnitCost)
                    dict_answ_temp["SKU"] = ProductSKU
                    dict_answ_temp["Discontinued"] = Discontinued
                    dict_answ_temp["DeliveryB"] = UnitPriceC
                    dict_answ_temp["ExpDate"] = ExpDate
                    dict_answ["data"].append(dict_answ_temp)

            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def createquoatallinfo(self, request: Request) -> Response:
        user_account = request.state.user
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            dict_answ = {
                "salesRep": [],
                "terms": [],
                "shipVia": [],
                "currentSalesRep": user_account["name"],
                "error": 0,
                "error_info": "",
            }
            with Session(engine[dict_form["DB"]]) as session:
                stmt_createquoatallinfo_salesRep = select(
                    Employees_tbl.__table__.columns,
                )
                rows_createquoatallinfo_salesRep = (
                    session.execute(stmt_createquoatallinfo_salesRep).mappings().all()
                )
                stmt_createquoatallinfo_Terms = select(
                    Terms_tbl.__table__.columns,
                )
                rows_createquoatallinfo_Terms = (
                    session.execute(stmt_createquoatallinfo_Terms).mappings().all()
                )
                stmt_createquoatallinfo_Shippers = select(
                    Shippers_tbl.__table__.columns,
                )
                rows_createquoatallinfo_Shippers = (
                    session.execute(stmt_createquoatallinfo_Shippers).mappings().all()
                )

                for i in rows_createquoatallinfo_salesRep:
                    dict_temp = {}
                    dict_temp.update({"id": i["EmployeeID"], "name": i["FirstName"]})
                    dict_answ["salesRep"].append(dict_temp)

                for i in rows_createquoatallinfo_Terms:
                    dict_temp = {}
                    dict_temp.update({"id": i["TermID"], "name": i["TermDescription"]})
                    dict_answ["terms"].append(dict_temp)

                for i in rows_createquoatallinfo_Shippers:
                    dict_temp = {}
                    dict_temp.update({"id": i["ShipperID"], "name": i["Shipper"]})
                    dict_answ["shipVia"].append(dict_temp)

            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def getbusinessinfo(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            with Session(engine[dict_form["DB"]]) as session:
                stmt_getbusinessinfo = (
                    select(
                        Customers_tbl.__table__.columns,
                    )
                    .filter_by(Discontinued=0)
                    .limit(100)
                )
                if dict_form["searchBy"] == "bnameInput":
                    stmt_getbusinessinfo = stmt_getbusinessinfo.filter(
                        Customers_tbl.BusinessName.like(f"{dict_form['searchValue']}%")
                    )
                elif dict_form["searchBy"] == "acnumInput":
                    stmt_getbusinessinfo = stmt_getbusinessinfo.filter(
                        Customers_tbl.AccountNo.like(f"{dict_form['searchValue']}%")
                    )

                rows_getbusinessinfo = (
                    session.execute(stmt_getbusinessinfo).mappings().all()
                )
            dict_answ = {"data": []}
            for i in rows_getbusinessinfo:
                dict_answ_temp = {}
                dict_ship_temp = {}
                dict_billing_temp = {}

                dict_ship_temp.update(
                    {
                        "street": i["ShipAddress1"],
                        "street2": i["ShipAddress2"],
                        "city": i["ShipCity"],
                        "state": i["ShipState"],
                        "zip": i["ShipZipCode"],
                        "contactName": i["ShipContact"],
                        "phone": i["ShipPhone_Number"],
                        "shipName": i["Shipto"],
                    }
                )
                dict_billing_temp.update(
                    {
                        "street": i["Address1"],
                        "street2": i["Address2"],
                        "city": i["City"],
                        "state": i["State"],
                        "zip": i["ZipCode"],
                        "contactName": i["Contactname"],
                        "phone": i["Phone_Number"],
                    }
                )

                dict_answ_temp.update(
                    {
                        "id": i["CustomerID"],
                        "bname": i["BusinessName"],
                        "anum": i["AccountNo"],
                    }
                )
                dict_answ_temp.update({"shippingAddress": dict_ship_temp})
                dict_answ_temp.update({"billingAddress": dict_billing_temp})
                dict_answ_temp.update({"termsid": i["TermID"]})
                dict_answ_temp.update({"Memo": i["Memo"]})
                dict_answ_temp.update({"error": 0})
                dict_answ_temp.update({"error_info": ""})
                dict_answ["data"].append(dict_answ_temp)
                dict_answ.update({"error": 0})
                dict_answ.update({"error_info": ""})

            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def getsupplier(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            with Session(engine[dict_form["DB"]]) as session:
                stmt_getsupplier = select(
                    Suppliers_tbl.__table__.columns,
                ).limit(20)

                if dict_form["searchBy"] == "bnameInput":
                    stmt_getsupplier = stmt_getsupplier.filter(
                        Suppliers_tbl.BusinessName.like(f"{dict_form['searchValue']}%")
                    )
                elif dict_form["searchBy"] == "acnumInput":
                    stmt_getsupplier = stmt_getsupplier.filter(
                        Suppliers_tbl.AccountNo.like(f"{dict_form['searchValue']}%")
                    )

                rows_getsupplier = session.execute(stmt_getsupplier).mappings().all()
            dict_answ = {"data": []}
            for i in rows_getsupplier:
                dict_answ_temp = {}
                dict_answ_temp.update(
                    {
                        "id": i["SupplierID"],
                        "bname": i["BusinessName"],
                        "anum": i["AccountNo"],
                        "Address1": i["Address1"],
                        "Address2": i["Address2"],
                        "State": i["State"],
                        "ZipCode": i["ZipCode"],
                        "Phone_Number": i["Phone_Number"],
                        "Contactname": i["Contactname"],
                        "Email": i["Email"],
                    }
                )

                dict_answ["data"].append(dict_answ_temp)

            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def savequotation(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            user_account = request.state.user

            # Basic form validation.
            required_fields = [
                "DB", "qnumber", "customerMemo", "accountnum", "QuotationID",
                "pricelevel", "CustomerID", "businessname", "shipto", "sstreet",
                "scity", "szip", "sphone", "shipvia", "terms", "srep", "qtotal", "items"
            ]
            missing = [f for f in required_fields if f not in dict_form]
            if missing:
                response = JSONResponse(
                    {"data_create_quotation": [{"error": 1, "error_info": f"Missing fields: {', '.join(missing)}"}]},
                    status_code=400
                )
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response

            qnumber = dict_form["qnumber"]
            SourceDB = dict_form["DB"]
            customerMemo = dict_form["customerMemo"]
            accountnum = dict_form["accountnum"]
            QuotationID = dict_form["QuotationID"]
            pricelevel = dict_form["pricelevel"].strip()
            ExpirationDate = (
                datetime.datetime.today() + datetime.timedelta(days=10)
            ).strftime("%Y-%m-%d 00:00:00")
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d 00:00:00")
            tn_ind = (datetime.datetime.today() - datetime.timedelta(hours=5)).strftime(
                "%m%d%Y"
            )
            time_now_5h_m = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            index = dict_form["DB"][-1]
            gen_new_n = int(f"{tn_ind}{index}")
            if "sstate" not in dict_form:
                dict_form["sstate"] = ""

            with Session(engine[dict_form["DB"]]) as session:
                stmt_up_cust = (
                    update(Customers_tbl)
                    .values(
                        Memo=customerMemo,
                    )
                    .where(Customers_tbl.AccountNo == accountnum)
                )
                answ_up_cust = session.execute(stmt_up_cust)

                # Items payload validation.
                try:
                    items_quotation_list = json.loads(dict_form["items"])
                    if not isinstance(items_quotation_list, list) or not items_quotation_list:
                        raise ValueError("items must be a non-empty list")
                except Exception:
                    response = JSONResponse(
                        {"data_create_quotation": [{"error": 1, "error_info": "Invalid items payload"}]},
                        status_code=400
                    )
                    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response

                # Normalize/validate each item and collect UPCs (no duplicates inside the request)
                # NOTE: To avoid [i][0] issue, keep compatible with dict/list-of-dict.
                upcs: list[str] = []
                norm_items: list[dict] = []
                try:
                    for i in items_quotation_list:
                        row = i if isinstance(i, dict) else (i[0] if isinstance(i, list) and i and isinstance(i[0], dict) else None)
                        if not row:
                            raise ValueError("Bad item format")

                        upc = str(row.get("UPC", "")).strip()
                        if not upc:
                            raise ValueError("UPC is required")

                        # Qty must be positive integer
                        qty = int(row.get("Qty", 0))
                        if qty <= 0:
                            raise ValueError(f"Qty must be > 0 for UPC {upc}")

                        # UnitPrice must be numeric
                        try:
                            float(row.get("UnitPrice", 0))
                        except Exception:
                            raise ValueError(f"UnitPrice must be numeric for UPC {upc}")

                        upcs.append(upc)
                        norm_items.append(row)
                except ValueError as ve:
                    response = JSONResponse(
                        {"data_create_quotation": [{"error": 1, "error_info": str(ve)}]},
                        status_code=400
                    )
                    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response

                dup_upcs = sorted({u for u in upcs if upcs.count(u) > 1})
                if dup_upcs:
                    response = JSONResponse(
                        {"data_create_quotation": [{"error": 1, "error_info": f"Duplicate items in request (UPC): {', '.join(dup_upcs)}"}]},
                        status_code=409
                    )
                    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response

                # Every UPC exists in Items_tbl (single query)
                if upcs:
                    stmt_check_items = select(Items_tbl.ProductUPC).where(Items_tbl.ProductUPC.in_(upcs))
                    found_upcs = {r[0] for r in session.execute(stmt_check_items).all()}
                    missing_upcs = sorted(set(upcs) - found_upcs)
                    if missing_upcs:
                        response = JSONResponse(
                            {"data_create_quotation": [{"error": 1, "error_info": f"Items not found by UPC: {', '.join(missing_upcs)}"}]},
                            status_code=400
                        )
                        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                        response.headers["Pragma"] = "no-cache"
                        response.headers["Expires"] = "0"
                        return response

                qty_l = []
                for i_items_quotation_list in items_quotation_list:
                    qty_l.append(i_items_quotation_list["Qty"])
                s_qty_l = sum(qty_l)

                if not qnumber:
                    with Session(engine["DB_admin"]) as sessiond:
                        new_QuotationNumber = generate_unique_quotation_number_with_prefix(
                            session_main=session,
                            session_admin=sessiond,
                            quotations_table=Quotations_tbl,
                            quotations_status_table=QuotationsStatus,
                            date_prefix=gen_new_n,
                        )
                    stmt = (
                        insert(Quotations_tbl)
                        .values(
                            QuotationNumber=new_QuotationNumber,
                            ExpirationDate=ExpirationDate,
                            QuotationDate=time_now_5h_m,
                            CustomerID=dict_form["CustomerID"],
                            BusinessName=dict_form["businessname"],
                            AccountNo=dict_form["accountnum"],
                            Shipto=dict_form["shipto"],
                            ShipAddress1=dict_form["sstreet"],
                            ShipAddress2=dict_form["sstreet2"],
                            ShipContact=dict_form["scname"],
                            ShipCity=dict_form["scity"],
                            ShipState=dict_form["sstate"],
                            ShipZipCode=dict_form["szip"],
                            ShipPhoneNo=dict_form["sphone"],
                            QuotationTitle=pricelevel,
                            Status=1,
                            ShipperID=dict_form["shipvia"],
                            flaged=0,
                            TermID=dict_form["terms"],
                            SalesRepID=dict_form["srep"],
                            QuotationTotal=dict_form["qtotal"],
                        )
                        .returning(
                            Quotations_tbl.QuotationID,
                        )
                    )
                    rows_quotation_insert = session.execute(stmt).mappings().all()
                    QuotationID = rows_quotation_insert[0]["QuotationID"]
                    query_employees = select(Employees_tbl.FirstName).where(
                        Employees_tbl.EmployeeID == dict_form["srep"]
                    )
                    answer_employees = (
                        session.execute(query_employees)
                        .mappings()
                        .all()[0]["FirstName"]
                        .strip()
                        .lower()
                    )
                    with Session(engine["DB_admin"]) as session1:
                        stmt_q_st = (
                            insert(QuotationsStatus)
                            .values(
                                DateCreate=time_now_5h_m,
                                LastUpdate=time_now_5h_m,
                                QuotationNumber=new_QuotationNumber,
                                SalesRep=answer_employees,
                                SourceDB=engine_db_nick_name[SourceDB],
                                BusinessName=dict_form["businessname"].replace(
                                    "'", "''"
                                ),
                                Status="New",
                                TotalQty=s_qty_l,
                                InvoiceNumber="",
                                AccountNo=dict_form["accountnum"],
                                Username=user_account["name"],
                                UserStatus=user_account["statususer"],
                                Shipto=dict_form["shipto"],
                                ShipAddress1=dict_form["sstreet"],
                                ShipAddress2=dict_form["sstreet2"],
                                ShipContact=dict_form["scname"],
                                ShipCity=dict_form["scity"],
                                ShipState=dict_form["sstate"],
                                ShipZipCode=dict_form["szip"],
                                ShipPhoneNo=dict_form["sphone"],
                                ShipperID=dict_form["shipvia"],
                                TermID=dict_form["terms"],
                                QuotationTotal=dict_form["qtotal"],
                                Dop1=QuotationID,
                            )
                            .returning(
                                QuotationsStatus.id,
                            )
                        )
                        rows_stmt_q_st = session1.execute(stmt_q_st).mappings().all()
                        session1.commit()

                    if items_quotation_list and QuotationID:
                        for i in items_quotation_list:
                            ProductUPC = [i][0]["UPC"]
                            ProductDescription = [i][0]["Description"]
                            UnitPrice = [i][0]["UnitPrice"]
                            ProductSKU = [i][0]["SKU"]
                            Qty = [i][0]["Qty"]
                            Comments = [i][0]["Comment"]
                            if "rememberprice" in [i][0]:
                                if [i][0]["rememberprice"]:
                                    rememberprice = 1
                                else:
                                    rememberprice = 0
                            else:
                                rememberprice = 0
                            stmt_quotation_items = select(
                                Items_tbl.__table__.columns
                            ).filter_by(ProductUPC=ProductUPC)
                            rows_quotation_items = (
                                session.execute(stmt_quotation_items).mappings().all()
                            )
                            stmt_quotation_UnitDesc = select(
                                Units_tbl.__table__.columns
                            ).filter_by(UnitID=str(rows_quotation_items[0]["UnitID"]))
                            rows_quotation_UnitDesc = (
                                session.execute(stmt_quotation_UnitDesc)
                                .mappings()
                                .all()
                            )
                            if rows_quotation_UnitDesc:
                                UnitDesc = rows_quotation_UnitDesc[0]["UnitDesc"]
                            else:
                                UnitDesc = ""
                            stmt_quotationsdetails = (
                                insert(QuotationsDetails_tbl)
                                .values(
                                    QuotationID=QuotationID,
                                    CateID=rows_quotation_items[0]["CateID"],
                                    SubCateID=rows_quotation_items[0]["SubCateID"],
                                    ProductID=rows_quotation_items[0]["ProductID"],
                                    ProductSKU=ProductSKU,
                                    ProductUPC=rows_quotation_items[0]["ProductUPC"],
                                    ProductDescription=ProductDescription,
                                    ItemSize=rows_quotation_items[0]["ItemSize"],
                                    ExpDate=ExpirationDate,
                                    RememberPrice=rememberprice,
                                    UnitPrice=round(float(UnitPrice), 2),
                                    OriginalPrice=round(float(UnitPrice), 2),
                                    UnitCost=rows_quotation_items[0]["UnitCost"],
                                    Qty=int(Qty),
                                    ItemWeight=rows_quotation_items[0]["ItemWeight"],
                                    Discount=0,
                                    ds_Percent=0,
                                    ExtendedPrice=round(float(UnitPrice), 2) * int(Qty),
                                    ExtendedCost=rows_quotation_items[0]["UnitCost"]
                                    * int(Qty),
                                    ExtendedDisc=0,
                                    PromotionID=0,
                                    PromotionLine=0,
                                    SPPromoted=0,
                                    Taxable=0,
                                    ItemTaxID=0,
                                    Catch=0,
                                    Flag=0,
                                    Comments=Comments,
                                    ActExtendedPrice=round(float(UnitPrice), 2)
                                    * int(Qty),
                                    UnitDesc=UnitDesc,
                                )
                                .returning(
                                    QuotationsDetails_tbl.LineID,
                                )
                            )

                            rows_quotationsdetails = (
                                session.execute(stmt_quotationsdetails).mappings().all()
                            )
                    dict_answ = {
                        "data_create_quotation": [
                            {
                                "QuotationID": QuotationID,
                                "qnumber": new_QuotationNumber,
                                "status": "create",
                                "status_quotation": "New",
                                "error": 0,
                                "error_info": "",
                            },
                        ]
                    }
                    session.commit()
                else:
                    QuotationID = dict_form["QuotationID"]
                    if QuotationID == "0":
                        dict_answ = {
                            "data_create_quotation": [
                                {
                                    "error": 1,
                                    "error_info": "QuotationID connot be 0",
                                },
                            ]
                        }
                        response = JSONResponse(dict_answ)
                        response.headers["Cache-Control"] = (
                            "no-store, no-cache, must-revalidate, max-age=0"
                        )
                        response.headers["Pragma"] = "no-cache"
                        response.headers["Expires"] = "0"

                        return response

                    with Session(engine["DB_admin"]) as session2:
                        stmt_update_answ = (
                            update(QuotationsStatus)
                            .values(
                                LastUpdate=time_now_5h_m,
                                TotalQty=s_qty_l,
                                AccountNo=dict_form["accountnum"],
                                Username=user_account["name"],
                                UserStatus=user_account["statususer"],
                                Shipto=dict_form["shipto"],
                                ShipAddress1=dict_form["sstreet"],
                                ShipAddress2=dict_form["sstreet2"],
                                ShipContact=dict_form["scname"],
                                ShipCity=dict_form["scity"],
                                ShipState=dict_form["sstate"],
                                ShipZipCode=dict_form["szip"],
                                ShipPhoneNo=dict_form["sphone"],
                                ShipperID=dict_form["shipvia"],
                                TermID=dict_form["terms"],
                                QuotationTotal=dict_form["qtotal"],
                                Dop1=QuotationID,
                            )
                            .where(
                                QuotationsStatus.Dop1 == QuotationID,
                            )
                        )
                        answ_update_answ = session2.execute(stmt_update_answ)
                        session2.commit()

                        stmt_check_sessions = select(
                            AuditLog.__table__.columns,
                        ).where(
                            and_(
                                AuditLog.QuotationID == QuotationID,
                                AuditLog.username != user_account["name"],
                                AuditLog.isClosed == 0,
                            )
                        )

                        rows_check_sessions = (
                            session2.execute(stmt_check_sessions).mappings().all()
                        )

                        if not rows_check_sessions:
                            stmt_update_answ = (
                                update(AuditLog)
                                .values(
                                    endDate=time_now_5h_m,
                                    isClosed=1,
                                )
                                .where(
                                    AuditLog.QuotationID == QuotationID,
                                    AuditLog.username == user_account["name"],
                                )
                            )
                            answ_update_answ = session2.execute(stmt_update_answ)
                            session2.commit()
                        else:
                            stmt_check_sessions1 = select(
                                AuditLog.__table__.columns,
                            ).where(
                                and_(
                                    AuditLog.QuotationID == QuotationID,
                                    AuditLog.username != user_account["name"],
                                    AuditLog.isClosed == 0,
                                )
                            )
                            rows_check_sessions1 = (
                                session2.execute(stmt_check_sessions1).mappings().all()
                            )
                            if rows_check_sessions1:
                                par_users: list[str] = list()
                                for i_rows_check_sessions1 in rows_check_sessions1:
                                    par_users.append(i_rows_check_sessions1["username"])

                                dict_answ = {
                                    "data_create_quotation": [
                                        {
                                            "error": 1,
                                            "error_info": f'The Quotation could not be saved, because it is open to the user {(" and ").join(par_users)}',
                                        },
                                    ]
                                }
                                response = JSONResponse(dict_answ)
                                response.headers["Cache-Control"] = (
                                    "no-store, no-cache, must-revalidate, max-age=0"
                                )
                                response.headers["Pragma"] = "no-cache"
                                response.headers["Expires"] = "0"
                                return response
                            else:
                                dict_answ = {
                                    "data_create_quotation": [
                                        {
                                            "error": 1,
                                            "error_info": f"Quotation connot be save, reopen it",
                                        },
                                    ]
                                }
                                response = JSONResponse(dict_answ)
                                response.headers["Cache-Control"] = (
                                    "no-store, no-cache, must-revalidate, max-age=0"
                                )
                                response.headers["Pragma"] = "no-cache"
                                response.headers["Expires"] = "0"
                                return response
                    stmt_update_quotationedit = (
                        update(Quotations_tbl)
                        .values(
                            QuotationDate=time_now_5h_m,
                            CustomerID=dict_form["CustomerID"],
                            BusinessName=dict_form["businessname"],
                            AccountNo=dict_form["accountnum"],
                            Shipto=dict_form["shipto"],
                            ShipAddress1=dict_form["sstreet"],
                            ShipAddress2=dict_form["sstreet2"],
                            ShipContact=dict_form["scname"],
                            ShipCity=dict_form["scity"],
                            ShipState=dict_form["sstate"],
                            ShipZipCode=dict_form["szip"],
                            ShipPhoneNo=dict_form["sphone"],
                            ShipperID=dict_form["shipvia"],
                            TermID=dict_form["terms"],
                            SalesRepID=dict_form["srep"],
                            QuotationTitle=pricelevel,
                            QuotationTotal=dict_form["qtotal"],
                        )
                        .where(Quotations_tbl.QuotationID == QuotationID)
                    )
                    answ_update_quotation_details = session.execute(
                        stmt_update_quotationedit
                    )
                    stmt_delete = delete(QuotationsDetails_tbl).where(
                        QuotationsDetails_tbl.QuotationID == QuotationID
                    )
                    answ_delete = session.execute(stmt_delete)
                    session.commit()
                    with Session(engine["DB_admin"]) as session20:
                        stmt_delete = delete(QuotationsInProgress).where(
                            QuotationsInProgress.tempField1 == QuotationID
                        )
                        answ_delete = session20.execute(stmt_delete)
                        session20.commit()
                    if items_quotation_list and QuotationID:
                        for i in items_quotation_list:
                            ProductUPC = [i][0]["UPC"]
                            ProductDescription = [i][0]["Description"]
                            UnitPrice = [i][0]["UnitPrice"]
                            ProductSKU = [i][0]["SKU"]
                            Qty = [i][0]["Qty"]
                            Comments = [i][0]["Comment"]
                            if "rememberprice" in [i][0]:
                                if [i][0]["rememberprice"]:
                                    rememberprice = 1
                                else:
                                    rememberprice = 0
                            else:
                                rememberprice = 0
                            stmt_quotation_items = select(
                                Items_tbl.__table__.columns
                            ).filter_by(ProductUPC=ProductUPC)
                            rows_quotation_items = (
                                session.execute(stmt_quotation_items).mappings().all()
                            )
                            ExtendedCost = rows_quotation_items[0]["UnitCost"]
                            if ExtendedCost == None:
                                ExtendedCost = 0
                            stmt_quotation_UnitDesc = select(
                                Units_tbl.__table__.columns
                            ).filter_by(UnitID=str(rows_quotation_items[0]["UnitID"]))
                            rows_quotation_UnitDesc = (
                                session.execute(stmt_quotation_UnitDesc)
                                .mappings()
                                .all()
                            )
                            if rows_quotation_UnitDesc:
                                UnitDesc = rows_quotation_UnitDesc[0]["UnitDesc"]
                            else:
                                UnitDesc = ""
                            stmt_quotationsdetails = (
                                insert(QuotationsDetails_tbl)
                                .values(
                                    QuotationID=QuotationID,
                                    CateID=rows_quotation_items[0]["CateID"],
                                    SubCateID=rows_quotation_items[0]["SubCateID"],
                                    ProductID=rows_quotation_items[0]["ProductID"],
                                    ProductSKU=ProductSKU,
                                    ProductUPC=rows_quotation_items[0]["ProductUPC"],
                                    ProductDescription=ProductDescription,
                                    ItemSize=rows_quotation_items[0]["ItemSize"],
                                    ExpDate=ExpirationDate,
                                    UnitPrice=round(float(UnitPrice), 2),
                                    OriginalPrice=round(float(UnitPrice), 2),
                                    UnitCost=rows_quotation_items[0]["UnitCost"],
                                    Qty=int(Qty),
                                    RememberPrice=rememberprice,
                                    ItemWeight=rows_quotation_items[0]["ItemWeight"],
                                    Discount=0,
                                    ds_Percent=0,
                                    ExtendedPrice=round(float(UnitPrice), 2) * int(Qty),
                                    ExtendedCost=ExtendedCost * int(Qty),
                                    ExtendedDisc=0,
                                    PromotionID=0,
                                    PromotionLine=0,
                                    SPPromoted=0,
                                    Taxable=0,
                                    ItemTaxID=0,
                                    Catch=0,
                                    Flag=0,
                                    Comments=Comments,
                                    ActExtendedPrice=round(float(UnitPrice), 2)
                                    * int(Qty),
                                    UnitDesc=UnitDesc,
                                )
                                .returning(
                                    QuotationsDetails_tbl.LineID,
                                )
                            )

                            rows_quotationsdetails = (
                                session.execute(stmt_quotationsdetails).mappings().all()
                            )
                    session.commit()
                    dict_answ = {
                        "data_create_quotation": [
                            {
                                "QuotationID": QuotationID,
                                "qnumber": qnumber,
                                "status": "update",
                                "error": 0,
                                "error_info": "",
                            },
                        ]
                    }
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response


    async def removeReadOnly(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            user_account = request.state.user["name"]
            SourceDBname = engine_db_nick_name[dict_form["DB"]]
            QuotationID = dict_form["QuotationID"]
            dict_answ = {
                "data_removeReadOnly": [
                    {
                        "QuotationID": QuotationID,
                    },
                ],
                "error": 0,
                "error_info": "",
            }
            time_now_5h_m = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            with Session(engine["DB_admin"]) as session2:
                stmt_check_sessions = (
                    select(
                        AuditLog.__table__.columns,
                    )
                    .where(
                        and_(
                            AuditLog.QuotationID == QuotationID,
                            AuditLog.isClosed == 0,
                        )
                    )
                    .order_by(AuditLog.QuotationID.desc())
                )
                rows_check_sessions = (
                    session2.execute(stmt_check_sessions).mappings().all()
                )
                if rows_check_sessions:
                    stmt_update_answ = (
                        update(AuditLog)
                        .values(
                            endDate=time_now_5h_m,
                            isClosed=1,
                        )
                        .where(
                            AuditLog.QuotationID == QuotationID,
                            AuditLog.quotationDB == SourceDBname,
                        )
                    )
                    answ_update_answ = session2.execute(stmt_update_answ)
                    if rows_check_sessions[0]["username"] != user_account:
                        stmt_ins_answ = (
                            insert(AuditLog)
                            .values(
                                QuotationID=QuotationID,
                                quotationDB=SourceDBname,
                                startDate=time_now_5h_m,
                                username=user_account,
                                eventType="ReadOnly",
                                isClosed=0,
                            )
                            .returning(
                                AuditLog.sessionID,
                            )
                        )
                        rows_ins_answ = session2.execute(stmt_ins_answ).mappings().all()
                        dict_answ.update({"error": 0})
                        dict_answ.update(
                            {"error_info": f"All sessions closed for this Quotation"}
                        )
                    session2.commit()
                else:
                    dict_answ.update({"error": 0})
                    dict_answ.update({"error_info": f"Users not edit this Quotation"})
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def savepo(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            PoID = dict_form["poid"]
            PoNumber = dict_form["PoNumber"]
            AccountNo = dict_form["accountnum"]
            ExpirationDate = (
                datetime.datetime.today() + datetime.timedelta(days=25)
            ).strftime("%Y-%m-%d 00:00:00")
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d 00:00:00")
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            isCommitAllowed = checkcomituser(statususer)
            commit_status = dict_form["status"]
            if commit_status == "1":
                dict_answ = {
                    "data": [],
                    "error": 1,
                    "error_info": "You cannot commit this Quotation",
                }
                response = JSONResponse(dict_answ)
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            with Session(engine[dict_form["DB"]]) as session:
                items_quotation_list = json.loads(dict_form["items"])
                stmt_Suppliers_tbl = select(Suppliers_tbl.__table__.columns).filter_by(
                    AccountNo=AccountNo
                )
                rows_Suppliers_tbl = (
                    session.execute(stmt_Suppliers_tbl).mappings().all()
                )
                SupplierID = rows_Suppliers_tbl[0]["SupplierID"]
                stmt_CompanyInfo_tbl = select(
                    CompanyInfo_tbl.__table__.columns,
                )
                rows_CompanyInfo_tbl = (
                    session.execute(stmt_CompanyInfo_tbl).mappings().all()
                )
                ShipContact = dict_form["contactname"]
                Shipto = rows_CompanyInfo_tbl[0]["CompanyName"]
                ShipAddress1 = rows_CompanyInfo_tbl[0]["Address1"]
                ShipAddress2 = rows_CompanyInfo_tbl[0]["Address2"]
                ShipCity = rows_CompanyInfo_tbl[0]["City"]
                ShipState = rows_CompanyInfo_tbl[0]["State"]
                ShipZipCode = rows_CompanyInfo_tbl[0]["ZipCode"]
                ShipPhoneNo = rows_CompanyInfo_tbl[0]["PhoneNumber"]
                if not PoID:
                    stmt_PurchaseOrders = select(
                        PurchaseOrders_tbl.__table__.columns
                    ).filter_by(PoNumber=PoNumber)
                    rows_PurchaseOrders = (
                        session.execute(stmt_PurchaseOrders).mappings().all()
                    )
                    if rows_PurchaseOrders:
                        dict_answ = {
                            "data": [],
                            "error": 1,
                            "error_info": "Purchase Order already present",
                        }
                        response = JSONResponse(dict_answ)
                        response.headers["Cache-Control"] = (
                            "no-store, no-cache, must-revalidate, max-age=0"
                        )
                        response.headers["Pragma"] = "no-cache"
                        response.headers["Expires"] = "0"
                        return response
                    stmt = (
                        insert(PurchaseOrders_tbl)
                        .values(
                            PoNumber=PoNumber,
                            PoDate=time_now_5h,
                            RequiredDate=time_now_5h,
                            SupplierID=SupplierID,
                            BusinessName=dict_form["businessname"],
                            AccountNo=dict_form["accountnum"],
                            PoTotal=dict_form["POTotal"],
                            EmployeeID=0,
                            NoLines=len(items_quotation_list),
                            ShipperID=0,
                            TotQtyOrd=dict_form["TotQtyOrd"],
                            TotQtyRcv=dict_form["TotQtyRcv"],
                            Shipto=Shipto,
                            ShipAddress1=ShipAddress1,
                            ShipAddress2=ShipAddress2,
                            ShipContact=ShipContact,
                            ShipCity=ShipCity,
                            ShipState=ShipState,
                            ShipZipCode=ShipZipCode,
                            ShipPhoneNo=ShipPhoneNo,
                        )
                        .returning(
                            PurchaseOrders_tbl.PoID,
                        )
                    )

                    rows_quotation_insert = session.execute(stmt).mappings().all()
                    PoID = rows_quotation_insert[0]["PoID"]
                    if items_quotation_list and PoID:
                        for i in items_quotation_list:
                            ProductUPC = [i][0]["UPC"]
                            ProductDescription = [i][0]["Description"]
                            UnitCost = [i][0]["UnitCost"]
                            ProductSKU = [i][0]["SKU"]
                            QtyOrdered = [i][0]["Qty"]
                            stmt_quotation_items = select(
                                Items_tbl.__table__.columns
                            ).filter_by(ProductUPC=ProductUPC)
                            rows_quotation_items = (
                                session.execute(stmt_quotation_items).mappings().all()
                            )
                            stmt_quotation_UnitDesc = select(
                                Units_tbl.__table__.columns
                            ).filter_by(UnitID=str(rows_quotation_items[0]["UnitID"]))
                            rows_quotation_UnitDesc = (
                                session.execute(stmt_quotation_UnitDesc)
                                .mappings()
                                .all()
                            )
                            if rows_quotation_UnitDesc:
                                UnitDesc = rows_quotation_UnitDesc[0]["UnitDesc"]
                            else:
                                UnitDesc = ""
                            stmt_quotationsdetails = (
                                insert(PurchaseOrdersDetails_tbl)
                                .values(
                                    PoID=PoID,
                                    CateID=rows_quotation_items[0]["CateID"],
                                    SubCateID=rows_quotation_items[0]["SubCateID"],
                                    ProductID=rows_quotation_items[0]["ProductID"],
                                    ProductSKU=ProductSKU,
                                    ProductUPC=rows_quotation_items[0]["ProductUPC"],
                                    ProductDescription=ProductDescription,
                                    ExpDate=ExpirationDate,
                                    UnitQty=1,
                                    UnitCost=UnitCost,
                                    ExtendedCost=round(float(UnitCost), 2)
                                    * int(QtyOrdered),
                                    QtyOrdered=int(QtyOrdered),
                                    QtyReceived=int(QtyOrdered),
                                )
                                .returning(
                                    PurchaseOrdersDetails_tbl.LineID,
                                )
                            )
                            rows_quotationsdetails = (
                                session.execute(stmt_quotationsdetails).mappings().all()
                            )
                    dict_answ = {
                        "data_create_po": [
                            {
                                "PoNumber": PoNumber,
                                "PoID": f"{PoID}",
                                "status": "create",
                                "error": 0,
                                "error_info": "",
                                "isCommitAllowed": isCommitAllowed,
                            },
                        ]
                    }
                    session.commit()
                else:
                    stmt_check_getquotation = select(
                        PurchaseOrders_tbl.__table__.columns,
                    ).filter_by(PoNumber=PoNumber)
                    rows_check_getquotation = (
                        session.execute(stmt_check_getquotation).mappings().all()
                    )
                    PoID = rows_check_getquotation[0]["PoID"]
                    stmt_update_quotationedit = (
                        update(PurchaseOrders_tbl)
                        .values(
                            PoDate=time_now_5h,
                            RequiredDate=time_now_5h,
                            SupplierID=SupplierID,
                            BusinessName=dict_form["businessname"],
                            AccountNo=dict_form["accountnum"],
                            PoTotal=dict_form["POTotal"],
                            NoLines=len(items_quotation_list),
                            TotQtyOrd=dict_form["TotQtyOrd"],
                            TotQtyRcv=dict_form["TotQtyRcv"],
                            Shipto=Shipto,
                            ShipAddress1=ShipAddress1,
                            ShipAddress2=ShipAddress2,
                            ShipContact=ShipContact,
                            ShipCity=ShipCity,
                            ShipState=ShipState,
                            ShipZipCode=ShipZipCode,
                            ShipPhoneNo=ShipPhoneNo,
                        )
                        .where(PurchaseOrders_tbl.PoID == PoID)
                    )
                    answ_update_quotation_details = session.execute(
                        stmt_update_quotationedit
                    )
                    stmt_delete = delete(PurchaseOrdersDetails_tbl).where(
                        PurchaseOrdersDetails_tbl.PoID == PoID
                    )
                    answ_delete = session.execute(stmt_delete)
                    session.commit()
                    if items_quotation_list and PoID:
                        for i in items_quotation_list:
                            ProductUPC = [i][0]["UPC"]
                            ProductDescription = [i][0]["Description"]
                            UnitCost = [i][0]["UnitCost"]
                            ProductSKU = [i][0]["SKU"]
                            QtyOrdered = [i][0]["Qty"]
                            stmt_quotation_items = select(
                                Items_tbl.__table__.columns
                            ).filter_by(ProductUPC=ProductUPC)
                            rows_quotation_items = (
                                session.execute(stmt_quotation_items).mappings().all()
                            )
                            stmt_quotation_UnitDesc = select(
                                Units_tbl.__table__.columns
                            ).filter_by(UnitID=str(rows_quotation_items[0]["UnitID"]))
                            rows_quotation_UnitDesc = (
                                session.execute(stmt_quotation_UnitDesc)
                                .mappings()
                                .all()
                            )
                            if rows_quotation_UnitDesc:
                                UnitDesc = rows_quotation_UnitDesc[0]["UnitDesc"]
                            else:
                                UnitDesc = ""

                            stmt_quotationsdetails = (
                                insert(PurchaseOrdersDetails_tbl)
                                .values(
                                    PoID=PoID,
                                    CateID=rows_quotation_items[0]["CateID"],
                                    SubCateID=rows_quotation_items[0]["SubCateID"],
                                    ProductID=rows_quotation_items[0]["ProductID"],
                                    ProductSKU=ProductSKU,
                                    UnitQty=1,
                                    ProductUPC=ProductUPC,
                                    ProductDescription=ProductDescription,
                                    ExpDate=ExpirationDate,
                                    UnitCost=UnitCost,
                                    ExtendedCost=round(float(UnitCost), 2)
                                    * int(QtyOrdered),
                                    QtyOrdered=int(QtyOrdered),
                                    QtyReceived=int(QtyOrdered),
                                )
                                .returning(
                                    PurchaseOrdersDetails_tbl.LineID,
                                )
                            )
                            rows_quotationsdetails = (
                                session.execute(stmt_quotationsdetails).mappings().all()
                            )
                    session.commit()
            dict_answ = {
                "data_create_po": [
                    {
                        "PoNumber": PoNumber,
                        "PoID": f"{PoID}",
                        "status": "update",
                        "error": 0,
                        "error_info": "",
                        "isCommitAllowed": isCommitAllowed,
                    },
                ]
            }
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def shippers(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d 00:00:00")
            SourceDB = dict_form["DB"]
            with Session(engine[SourceDB]) as session:
                query_ship = select(
                    Shippers_tbl.__table__.columns,
                )
                answ_query_ship = session.execute(query_ship).mappings().all()
            for i in answ_query_ship:
                dict_temp: dict[str:str] = dict()
                dict_temp.update({"shipperID": i["ShipperID"]})
                dict_temp.update({"shipperName": i["Shipper"]})
                dict_answ["data"].append(dict_temp)
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def setprogress(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            QuotationNumber = dict_form["QuotationNumber"]
            SourceDB = dict_form["DB"]
            QuotationID = dict_form["QuotationID"]
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            with Session(engine[SourceDB]) as session:
                query_Quotation = (
                    select(
                        Quotations_tbl.__table__.columns,
                        QuotationsDetails_tbl.__table__.columns,
                    )
                    .join(
                        QuotationsDetails_tbl,
                        Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                    )
                    .where(Quotations_tbl.QuotationID == QuotationID)
                )

                answ_Quotation = session.execute(query_Quotation).mappings().all()

            with Session(engine["DB_admin"]) as session:
                query_checkactivequotations = select(
                    QuotationsInProgress.__table__.columns
                ).filter_by(tempField1=QuotationID)
                answ_checkactivequotations = (
                    session.execute(query_checkactivequotations).mappings().all()
                )
                if answ_checkactivequotations:
                    dict_answ = {
                        "data_set_progress": {
                            "error": 1,
                            "error_info": "Quotation already in progress",
                        }
                    }
                    response = JSONResponse(dict_answ)
                    response.headers["Cache-Control"] = (
                        "no-store, no-cache, must-revalidate, max-age=0"
                    )
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
                else:
                    for i in answ_Quotation:
                        query_set_progress = (
                            insert(QuotationsInProgress)
                            .values(
                                StartDate=time_now_5h,
                                Packer=engine_name_nick[SourceDB],
                                SourceDB=engine_db_nick_name[SourceDB],
                                Status="InProgress",
                                QuotationNumber=QuotationNumber,
                                AccountNo=i["AccountNo"],
                                SalesRepID=i["SalesRepID"],
                                ProductDescription=i["ProductDescription"],
                                ProductUPC=i["ProductUPC"],
                                ProductSKU=i["ProductSKU"],
                                Qty=i["Qty"],
                                CateID=i["CateID"],
                                SubCateID=i["SubCateID"],
                                tempField1=i["QuotationID"],
                            )
                            .returning(
                                QuotationsInProgress.id,
                            )
                        )
                        answ_query_set_progress = (
                            session.execute(query_set_progress).mappings().all()
                        )
                session.commit()
            dict_answ = {
                "data_set_progress": {
                    "error": 0,
                    "error_info": "",
                }
            }
        response = JSONResponse(dict_answ)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def updatequtationstatus(self, request: Request) -> Response:
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            user_account = request.state.user["name"]
            statususer = request.state.user["statususer"].strip().lower()
            QuotationNumber = dict_form["QuotationNumber"]
            NStat = dict_form["NewStatus"]
            OStat = dict_form["OldStatus"]
            DBname = dict_form["DBname"]
            QuotationID = dict_form["QuotationID"]

            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            dict_answ = {
                "data_updatequtationstatus": {
                    "error": 0,
                    "error_info": "",
                }
            }
            with Session(engine[DBname]) as session:
                query_quotation = (
                    select(
                        Quotations_tbl.__table__.columns,
                        QuotationsDetails_tbl.__table__.columns,
                    )
                    .join(
                        QuotationsDetails_tbl,
                        Quotations_tbl.QuotationID == QuotationsDetails_tbl.QuotationID,
                    )
                    .where(Quotations_tbl.QuotationID == QuotationID)
                )
                answ_quotation = session.execute(query_quotation).mappings().all()
            if OStat == "New" and NStat == "In Progress":
                with Session(engine["DB_admin"]) as session:
                    for i in answ_quotation:
                        query_set_progress = (
                            insert(QuotationsInProgress)
                            .values(
                                StartDate=time_now_5h,
                                Packer=engine_db_nick_name[DBname],
                                SourceDB=engine_db_nick_name[DBname],
                                Status="In Progress",
                                QuotationNumber=QuotationNumber,
                                AccountNo=i["AccountNo"],
                                SalesRepID=i["SalesRepID"],
                                ProductDescription=i["ProductDescription"],
                                ProductUPC=i["ProductUPC"],
                                ProductSKU=i["ProductSKU"],
                                Qty=i["Qty"],
                                CateID=i["CateID"],
                                SubCateID=i["SubCateID"],
                                tempField1=i["QuotationID"],
                            )
                            .returning(
                                QuotationsInProgress.id,
                            )
                        )
                        answ_query_set_progress = (
                            session.execute(query_set_progress).mappings().all()
                        )
                        stmt_update_qs = (
                            update(QuotationsStatus)
                            .values(
                                LastUpdate=time_now_5h,
                                Status=NStat,
                            )
                            .where(QuotationsStatus.Dop1 == QuotationID)
                        )
                        answ_update_qs = session.execute(stmt_update_qs)
                    session.commit()
            elif (OStat == "In Progress" or OStat == "Locked") and NStat == "New":
                with Session(engine["DB_admin"]) as session:
                    stmt_delete = delete(QuotationsInProgress).where(
                        QuotationsInProgress.tempField1 == QuotationID
                    )
                    answ_delete = session.execute(stmt_delete)
                    stmt_update_qs = (
                        update(QuotationsStatus)
                        .values(
                            LastUpdate=time_now_5h,
                            Status=NStat,
                        )
                        .where(QuotationsStatus.Dop1 == QuotationID)
                    )
                    answ_update_qs = session.execute(stmt_update_qs)
                    session.commit()

            elif OStat == "Locked" and NStat == "In Progress":
                with Session(engine["DB_admin"]) as session:
                    stmt_update_qs = (
                        update(QuotationsStatus)
                        .values(
                            LastUpdate=time_now_5h,
                            Status=NStat,
                        )
                        .where(QuotationsStatus.Dop1 == QuotationID)
                    )
                    answ_update_qs = session.execute(stmt_update_qs)
                    session.commit()

            elif OStat == "In Progress" and NStat == "Locked":
                with Session(engine["DB_admin"]) as session:
                    stmt_update_qs = (
                        update(QuotationsStatus)
                        .values(
                            LastUpdate=time_now_5h,
                            Status=NStat,
                            Checker=user_account,
                        )
                        .where(QuotationsStatus.Dop1 == QuotationID)
                    )
                    answ_update_qs = session.execute(stmt_update_qs)

                    stmt_update_qs = (
                        update(QuotationsInProgress)
                        .values(
                            EndDate=time_now_5h,
                            Status=NStat,
                            Checker=user_account,
                        )
                        .where(QuotationsInProgress.tempField1 == QuotationID)
                    )
                    answ_update_qs = session.execute(stmt_update_qs)

                    session.commit()

            elif OStat == "Locked" and NStat == "New":
                with Session(engine["DB_admin"]) as session:
                    stmt_delete = delete(QuotationsInProgress).where(
                        QuotationsInProgress.tempField1 == QuotationID
                    )
                    answ_delete = session.execute(stmt_delete)
                    stmt_update_qs = (
                        update(QuotationsStatus)
                        .values(
                            LastUpdate=time_now_5h,
                            Status=NStat,
                        )
                        .where(QuotationsStatus.Dop1 == QuotationID)
                    )
                    answ_update_qs = session.execute(stmt_update_qs)
                    session.commit()

            elif OStat == "Status Error" and NStat == "New":
                with Session(engine["DB_admin"]) as session33:

                    stmt_q_st = (
                        insert(QuotationsStatus)
                        .values(
                            DateCreate=time_now_5h,
                            LastUpdate=time_now_5h,
                            QuotationNumber=QuotationNumber,
                            SalesRep=answ_quotation[0]["SalesRepID"],
                            SourceDB=engine_db_nick_name[DBname],
                            BusinessName=answ_quotation[0]["BusinessName"].replace(
                                "'", "''"
                            ),
                            Status="New",
                            TotalQty=sum([i["Qty"] for i in answ_quotation]),
                            InvoiceNumber="",
                            AccountNo=answ_quotation[0]["AccountNo"],
                            Username=user_account,
                            UserStatus=statususer,
                            Shipto=answ_quotation[0]["Shipto"],
                            ShipAddress1=answ_quotation[0]["ShipAddress1"],
                            ShipAddress2=answ_quotation[0]["ShipAddress2"],
                            ShipContact=answ_quotation[0]["ShipContact"],
                            ShipCity=answ_quotation[0]["ShipCity"],
                            ShipState=answ_quotation[0]["ShipState"],
                            ShipZipCode=answ_quotation[0]["ShipZipCode"],
                            ShipPhoneNo=answ_quotation[0]["ShipPhoneNo"],
                            ShipperID=answ_quotation[0]["ShipperID"],
                            TermID=answ_quotation[0]["TermID"],
                            QuotationTotal=int(answ_quotation[0]["QuotationTotal"]),
                            Dop1=QuotationID,
                        )
                        .returning(
                            QuotationsStatus.id,
                        )
                    )
                    rows_stmt_q_st = session33.execute(stmt_q_st).mappings().all()
                    session33.commit()

            elif OStat == "Status Error" and NStat == "In Progress":
                with Session(engine["DB_admin"]) as session34:

                    query_checkactivequotations = select(
                        QuotationsStatus.__table__.columns
                    ).filter_by(Dop1=QuotationID)
                    answ_checkactivequotations = (
                        session34.execute(query_checkactivequotations).mappings().all()
                    )
                    if answ_checkactivequotations:
                        stmt_update_qs = (
                            update(QuotationsStatus)
                            .values(
                                LastUpdate=time_now_5h,
                                Status=NStat,
                            )
                            .where(QuotationsStatus.Dop1 == QuotationID)
                        )
                        answ_update_qs = session34.execute(stmt_update_qs)
                    else:
                        stmt_q_st = (
                            insert(QuotationsStatus)
                            .values(
                                DateCreate=time_now_5h,
                                LastUpdate=time_now_5h,
                                QuotationNumber=QuotationNumber,
                                SalesRep=answ_quotation[0]["SalesRepID"],
                                SourceDB=engine_db_nick_name[DBname],
                                BusinessName=answ_quotation[0]["BusinessName"].replace(
                                    "'", "''"
                                ),
                                Status="In Progress",
                                TotalQty=sum([i["Qty"] for i in answ_quotation]),
                                InvoiceNumber="",
                                AccountNo=answ_quotation[0]["AccountNo"],
                                Username=user_account,
                                UserStatus=statususer,
                                Shipto=answ_quotation[0]["Shipto"],
                                ShipAddress1=answ_quotation[0]["ShipAddress1"],
                                ShipAddress2=answ_quotation[0]["ShipAddress2"],
                                ShipContact=answ_quotation[0]["ShipContact"],
                                ShipCity=answ_quotation[0]["ShipCity"],
                                ShipState=answ_quotation[0]["ShipState"],
                                ShipZipCode=answ_quotation[0]["ShipZipCode"],
                                ShipPhoneNo=answ_quotation[0]["ShipPhoneNo"],
                                ShipperID=answ_quotation[0]["ShipperID"],
                                TermID=answ_quotation[0]["TermID"],
                                QuotationTotal=int(answ_quotation[0]["QuotationTotal"]),
                                Dop1=QuotationID,
                            )
                            .returning(
                                QuotationsStatus.id,
                            )
                        )
                        rows_stmt_q_st = session34.execute(stmt_q_st).mappings().all()

                    for i in answ_quotation:
                        query_set_progress = (
                            insert(QuotationsInProgress)
                            .values(
                                StartDate=time_now_5h,
                                Packer=engine_db_nick_name[DBname],
                                SourceDB=engine_db_nick_name[DBname],
                                Status="In Progress",
                                QuotationNumber=QuotationNumber,
                                AccountNo=i["AccountNo"],
                                SalesRepID=i["SalesRepID"],
                                ProductDescription=i["ProductDescription"],
                                ProductUPC=i["ProductUPC"],
                                ProductSKU=i["ProductSKU"],
                                Qty=i["Qty"],
                                CateID=i["CateID"],
                                SubCateID=i["SubCateID"],
                                tempField1=i["QuotationID"],
                            )
                            .returning(
                                QuotationsInProgress.id,
                            )
                        )
                        answ_query_set_progress = (
                            session34.execute(query_set_progress).mappings().all()
                        )

                    session34.commit()

            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def getquotation(self, request: Request) -> Response:
        query_string = urllib.parse.unquote_plus(
            request.__dict__["scope"]["query_string"].decode("utf-8")
        )
        query_string_getquotation = dict(parse_qsl(urlsplit(str(request.url)).query))
        if request.method == "GET":
            form = await request.form()
            identity = request.path_params.get("identity")
            dict_form = dict(form)
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            DB_getquotation = engine_nick[query_string_getquotation["DBname"]]
            QuotationNumber = query_string_getquotation["QuotationNumber"]
            QuotationID = query_string_getquotation["QuotationID"]
            user_account = request.state.user["name"].strip().lower()
            with Session(engine[DB_getquotation]) as session:
                stmt_check_getquotation = select(
                    Quotations_tbl.__table__.columns,
                ).filter_by(QuotationID=QuotationID)
                rows_check_getquotation = (
                    session.execute(stmt_check_getquotation).mappings().all()
                )
                AccountNo = rows_check_getquotation[0]["AccountNo"]
                stmt_check_getquotation_CustomerID = select(
                    Customers_tbl.__table__.columns,
                ).filter_by(CustomerID=rows_check_getquotation[0]["CustomerID"])
                rows_check_getquotation_CustomerID = (
                    session.execute(stmt_check_getquotation_CustomerID).mappings().all()
                )
                InvoiceNumber = rows_check_getquotation[0]["AutoOrderNo"]
                user_account_status = request.state.user["statususer"].strip().lower()
                isManager = 0
                isAdmin = 0
                if "manager" in user_account_status.split("/"):
                    isManager = 1
                if "admin" in user_account_status.split("/"):
                    isAdmin = 1
                dict_answ = {
                    "InvoiceNumber": InvoiceNumber,
                    "QuotationID": rows_check_getquotation[0]["QuotationID"],
                    "DB": DB_getquotation,
                    "qnumber": QuotationNumber,
                    "qdate": rows_check_getquotation[0]["QuotationDate"].strftime(
                        "%m-%d-%Y"
                    ),
                    "isManager": isManager,
                    "isAdmin": isAdmin,
                    "accountnum": rows_check_getquotation[0]["AccountNo"],
                    "businessname": rows_check_getquotation[0]["BusinessName"],
                    "CustomerID": rows_check_getquotation[0]["CustomerID"],
                    "srep": rows_check_getquotation[0]["SalesRepID"],
                    "shipto": rows_check_getquotation[0]["Shipto"],
                    "sstreet": rows_check_getquotation[0]["ShipAddress1"],
                    "sstreet2": rows_check_getquotation[0]["ShipAddress2"],
                    "scity": rows_check_getquotation[0]["ShipCity"],
                    "sstate": rows_check_getquotation[0]["ShipState"],
                    "szip": rows_check_getquotation[0]["ShipZipCode"],
                    "scname": rows_check_getquotation[0]["ShipContact"],
                    "sphone": rows_check_getquotation[0]["ShipPhoneNo"],
                    "shipvia": rows_check_getquotation[0]["ShipperID"],
                    "terms": rows_check_getquotation[0]["TermID"],
                    "bstreet": rows_check_getquotation_CustomerID[0]["Address1"],
                    "bstreet2": rows_check_getquotation_CustomerID[0]["Address2"],
                    "bcity": rows_check_getquotation_CustomerID[0]["City"],
                    "bstate": rows_check_getquotation_CustomerID[0]["State"],
                    "bzip": rows_check_getquotation_CustomerID[0]["ZipCode"],
                    "bcname": rows_check_getquotation_CustomerID[0]["Contactname"],
                    "bphone": rows_check_getquotation_CustomerID[0]["Phone_Number"],
                    "pricelevel": rows_check_getquotation[0]["QuotationTitle"],
                    "qtotal": int(rows_check_getquotation[0]["QuotationTotal"]),
                    "items": [],
                    "error": 0,
                    "error_info": "",
                }

                with Session(engine["DB_admin"]) as session11:
                    query_checkactivequotations = select(
                        QuotationsStatus.__table__.columns
                    ).filter_by(Dop1=QuotationID)
                    rows_StatusQuotation = (
                        session11.execute(query_checkactivequotations).mappings().all()
                    )
                if rows_StatusQuotation:
                    dict_answ.update(
                        {"StatusQuotation": rows_StatusQuotation[0]["Status"]}
                    )
                else:
                    dict_answ.update({"StatusQuotation": "Status Error"})

                if InvoiceNumber:
                    dict_answ.update({"StatusQuotation": "Converted"})

                stmt_check_QuotationsDetails = select(
                    QuotationsDetails_tbl.__table__.columns,
                ).filter_by(QuotationID=rows_check_getquotation[0]["QuotationID"])
                rows_check_QuotationsDetails = (
                    session.execute(stmt_check_QuotationsDetails).mappings().all()
                )
            if rows_check_QuotationsDetails:
                with Session(engine["DB1"]) as session1:
                    for i in rows_check_QuotationsDetails:
                        ProductUPC = i["ProductUPC"]
                        dict_check_QuotationsDetails = {}
                        ProductUPC = i["ProductUPC"]
                        ProductDescription = i["ProductDescription"]
                        UnitPrice = i["UnitPrice"]
                        UnitCost = i["UnitCost"]
                        if UnitCost == None:
                            UnitCost = 0
                        ProductSKU = i["ProductSKU"]
                        rememberprice = i["RememberPrice"]
                        if i["Comments"] == None:
                            Comment = ""
                        else:
                            Comment = i["Comments"]
                        if rememberprice == True:
                            rememberprice = 1
                        else:
                            rememberprice = 0
                        stmt_checkdb1 = select(
                            Items_tbl.QuantOnHand,
                        ).filter_by(ProductUPC=ProductUPC)
                        rows_checkdb1 = session1.execute(stmt_checkdb1).mappings().all()
                        if rows_checkdb1:
                            Stock = int(rows_checkdb1[0]["QuantOnHand"])
                        else:
                            Stock = 0
                        dict_check_QuotationsDetails.update(
                            {
                                "UPC": ProductUPC,
                                "Description": ProductDescription,
                                "UnitPrice": float(UnitPrice),
                                "UnitCost": float(UnitCost),
                                "SKU": ProductSKU,
                                "Qty": i["Qty"],
                                "Total": float(i["ExtendedPrice"]),
                                "Comment": Comment,
                                "rememberprice": rememberprice,
                                "TotalCost": float(i["ExtendedCost"]),
                                "Stock": int(Stock),
                            }
                        )
                        dict_answ["items"].append(dict_check_QuotationsDetails)

            with Session(engine["DB_admin"]) as session2:
                stmt_check_sessions = (
                    select(
                        AuditLog.__table__.columns,
                    )
                    .where(
                        and_(
                            AuditLog.QuotationID == QuotationID,
                            AuditLog.isClosed == 0,
                        )
                    )
                    .order_by(AuditLog.QuotationID.desc())
                )

                rows_check_sessions = (
                    session2.execute(stmt_check_sessions).mappings().all()
                )
                if not rows_check_sessions:
                    dict_answ.update({"ReadOnly": 0})
                    dict_answ.update({"ReadOnlyUser": ""})
                    dict_answ.update({"ReadOnlyTime": ""})

                    stmt_ins_answ = (
                        insert(AuditLog)
                        .values(
                            QuotationID=QuotationID,
                            quotationDB=query_string_getquotation["DBname"],
                            startDate=time_now_5h,
                            username=user_account,
                            eventType="ReadOnly",
                            isClosed=0,
                        )
                        .returning(
                            AuditLog.sessionID,
                        )
                    )
                    rows_ins_answ = session2.execute(stmt_ins_answ).mappings().all()
                    session2.commit()
                else:
                    if rows_check_sessions[0]["username"] == user_account:
                        dict_answ.update({"ReadOnly": 0})
                        dict_answ.update({"ReadOnlyUser": ""})
                        dict_answ.update({"ReadOnlyTime": ""})

                    else:
                        dict_answ.update({"error": 1})
                        dict_answ.update(
                            {"error_info": f"User already edit this Quotation"}
                        )
                        dict_answ.update({"ReadOnly": 1})
                        dict_answ.update(
                            {"ReadOnlyUser": rows_check_sessions[0]["username"]}
                        )
                        dict_answ.update(
                            {
                                "ReadOnlyTime": rows_check_sessions[0][
                                    "startDate"
                                ].strftime("%Y-%m-%d %I:%M %p")
                            }
                        )
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def updatepricelevel(self, request: Request) -> Response:
        dict_answ = {"Items": []}
        if request.method == "POST":
            form = await request.form()
            dict_form = dict(form)
            item_l = json.loads(dict_form["Items"])
            Pricelevel = dict_form["Pricelevel"]
            AccountNo = dict_form["anum"]
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            with Session(engine[dict_form["DB"]]) as session:
                for i in item_l:
                    stmt_prl = select(Items_tbl.__table__.columns).filter_by(
                        ProductUPC=i
                    )
                    rows_prl = session.execute(stmt_prl).mappings().all()
                    if not rows_prl:
                        continue
                    price_st = round(float(rows_prl[0]["UnitPrice"]), 2)
                    price_c = round(float(rows_prl[0]["UnitPriceC"]), 2)
                    if Pricelevel == "custom":
                        stmt_pr_in = (
                            select(
                                Invoices_tbl.InvoiceNumber,
                                Invoices_tbl.InvoiceDate,
                                InvoicesDetails_tbl.UnitPrice,
                                InvoicesDetails_tbl.ProductUPC,
                            )
                            .join(
                                Invoices_tbl,
                                Invoices_tbl.InvoiceID == InvoicesDetails_tbl.InvoiceID,
                            )
                            .where(
                                and_(
                                    Invoices_tbl.Void == 0,
                                    Invoices_tbl.InvoiceTitle not in ch_lis,
                                    Invoices_tbl.AccountNo == AccountNo,
                                    InvoicesDetails_tbl.ProductUPC == i,
                                    InvoicesDetails_tbl.RememberPrice == 1,
                                )
                            )
                            .order_by(Invoices_tbl.InvoiceNumber.desc())
                        )
                        rows_pr_in = session.execute(stmt_pr_in).mappings().all()
                        if rows_pr_in:
                            dict_answ["Items"].append(
                                {f"{i}": rows_pr_in[0]["UnitPrice"]}
                            )
                        else:
                            dict_answ["Items"].append({f"{i}": price_st})
                    elif Pricelevel == "standard":
                        dict_answ["Items"].append({f"{i}": price_st})
                    elif Pricelevel == "deliveryb":
                        dict_answ["Items"].append({f"{i}": price_c})
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def deleteeditquotation(self, request: Request) -> Response:
        dict_answ = {"data": []}
        if request.method == "POST":
            form = await request.form()
            identity = request.path_params.get("identity")
            dict_form = dict(form)
            time_now_5h = (
                datetime.datetime.today() - datetime.timedelta(hours=5)
            ).strftime("%Y-%m-%d %H:%M:%S")
            QuotationID = dict_form["QuotationID"]
            with Session(engine[dict_form["DBname"]]) as session:
                query_qtydel = select(Quotations_tbl.QuotationNumber).where(
                    Quotations_tbl.QuotationID == QuotationID
                )
                answer_qtydel = session.execute(query_qtydel).mappings().all()
                QuotationNumber = answer_qtydel[0]["QuotationNumber"]
                stmt_delete_qdet = delete(QuotationsDetails_tbl).where(
                    QuotationsDetails_tbl.QuotationID == QuotationID
                )
                answ_delete = session.execute(stmt_delete_qdet)

                stmt_delete_q = delete(Quotations_tbl).where(
                    Quotations_tbl.QuotationID == QuotationID
                )
                answ_delete = session.execute(stmt_delete_q)

                session.commit()

            with Session(engine["DB_admin"]) as session2:
                stmt_delete = delete(QuotationsInProgress).where(
                    QuotationsInProgress.tempField1 == QuotationID
                )
                answ_delete = session2.execute(stmt_delete)

                stmt_update_qs = (
                    update(QuotationsStatus)
                    .values(
                        LastUpdate=time_now_5h,
                        Status="DELETED",
                    )
                    .where(QuotationsStatus.Dop1 == QuotationID)
                )
                answ_update_qs = session2.execute(stmt_update_qs)

                session2.commit()

            dict_answ = {
                "data_create_quotation": [
                    {
                        "error": 0,
                        "error_info": "",
                    },
                ]
            }
            response = JSONResponse(dict_answ)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    async def _render_edit(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_edit(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        pk = request.path_params.get("pk")
        obj = await model.find_by_pk(request, pk)
        if obj is None:
            raise HTTPException(HTTP_404_NOT_FOUND)
        if request.method == "GET":
            return self.templates.TemplateResponse(
                model.edit_template,
                {
                    "request": request,
                    "model": model,
                    "raw_obj": obj,
                    "obj": await model.serialize(obj, request, RequestAction.EDIT),
                    "menu": menu(request),
                },
            )
        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.EDIT)
        try:
            obj = await model.edit(request, pk, dict_obj)
        except FormValidationError as exc:
            return self.templates.TemplateResponse(
                model.edit_template,
                {
                    "request": request,
                    "model": model,
                    "errors": exc.errors,
                    "obj": dict_obj,
                    "menu": menu(request),
                },
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )
        pk = getattr(obj, model.pk_attr)  # type: ignore
        url = request.url_for(self.route_name + ":list", identity=model.identity)
        if form.get("_continue_editing", None) is not None:
            url = request.url_for(
                self.route_name + ":edit", identity=model.identity, pk=pk
            )
        elif form.get("_add_another", None) is not None:
            url = request.url_for(self.route_name + ":create", identity=model.identity)
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    async def _render_edit1(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_edit(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        pk = request.path_params.get("pk")
        obj = await model.find_by_pk(request, pk)
        if obj is None:
            raise HTTPException(HTTP_404_NOT_FOUND)
        if request.method == "GET":
            return self.templates.TemplateResponse(
                model.edit_template,
                {
                    "request": request,
                    "model": model,
                    "raw_obj": obj,
                    "obj": await model.serialize(obj, request, RequestAction.EDIT),
                    "menu": menu(request),
                },
            )
        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.EDIT)

        try:
            obj = await model.edit1(request, pk, dict_obj)
        except FormValidationError as exc:
            raise HTTPException(HTTP_404_NOT_FOUND)
        return RedirectResponse(
            url="/project/items_tbl/list", status_code=HTTP_303_SEE_OTHER
        )

        if form.get("_continue_editing", None) is not None:
            return RedirectResponse(
                url="/project/items_tbl/list", status_code=HTTP_303_SEE_OTHER
            )

        elif form.get("_add_another", None) is not None:
            return RedirectResponse(
                url="/project/items_tbl/list", status_code=HTTP_303_SEE_OTHER
            )

    async def _render_error(
        self,
        request: Request,
        exc: Exception = HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR),
    ) -> Response:
        assert isinstance(exc, HTTPException)

        response = self.templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "exc": exc,
                "menu": menu(request),
            },
            status_code=exc.status_code,
        )
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def form_to_dict(
        self,
        request: Request,
        form_data: FormData,
        model: BaseModelView,
        action: RequestAction,
    ) -> Dict[str, Any]:
        data = {}
        for field in model.fields:
            if (action == RequestAction.EDIT and field.exclude_from_edit) or (
                action == RequestAction.CREATE and field.exclude_from_create
            ):
                continue
            data[field.name] = await field.parse_form_data(request, form_data, action)
        return data

    def mount_to(self, app: Starlette) -> None:
        admin_app = Starlette(
            routes=self.routes,
            middleware=self.middlewares,
            debug=self.debug,
            exception_handlers={HTTPException: self._render_error},
        )
        admin_app.state.ROUTE_NAME = self.route_name
        app.mount(
            self.base_url,
            app=admin_app,
            name=self.route_name,
        )
