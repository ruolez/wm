import os
from datetime import datetime
from api1.api_v2.api import admin_stop_all_syncs, admin_sync_all_accounts, get_customer_email, get_default_home_page, get_invoice_info, get_session_info, get_shippers, get_time_range, get_user_access_menu, get_user_accounts, get_user_role, set_default_home_page, set_sync_accounts, set_time_range, update_invoice_data
from api1.config import SECRET, CORS_ORIGINS
from api1.helpers import fetch_user_menu_and_default
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette_admin import DropDown
from starlette_admin.views import Link
from . import engine, query_f, select
from .admins.model import *
from .users.model import *
from .admins.schemas import *
from .users.schemas import *
from .admins.view import *
from .users.view import *
from .admins.provider import MyAuthProvider
from .storage import configure_storage
from starlette_admin.contrib.sqla import Admin

app = Starlette(
    routes=[
        Mount("/static", app=StaticFiles(directory="api1/static"), name="static"),
        Route(
            "/",
            lambda r: RedirectResponse(url="/project"),
        ),
    ],
    on_startup=[configure_storage],
)

app.add_middleware(SessionMiddleware, secret_key=SECRET)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.routes.append(Route("/api/update_invoice_data/{db}/", update_invoice_data, methods=["GET"]))
app.routes.append(Route("/api/get_shippers/{db}/", get_shippers, methods=["GET"]))
app.routes.append(Route("/api/get_user_role/{username}", get_user_role, methods=["GET"]))
app.routes.append(Route("/api/get_session_info/", get_session_info, methods=["GET"]))
app.routes.append(Route("/api/get_invoice_info/", get_invoice_info, methods=["GET"]))
app.routes.append(Route("/api/get_customer_email/{db}/{account_no}/", get_customer_email, methods=["GET"]))
app.routes.append(Route("/api/get_time_range/", get_time_range, methods=["GET"]))
app.routes.append(Route("/api/set_time_range/", set_time_range, methods=["POST"]))
app.routes.append(Route("/api/get_user_accounts/", get_user_accounts, methods=["GET"]))
app.routes.append(Route("/api/set_sync_accounts/", set_sync_accounts, methods=["POST"]))
app.routes.append(Route("/api/admin/sync_all_accounts/", admin_sync_all_accounts, methods=["POST"]))
app.routes.append(Route("/api/admin/stop_all_sync/", admin_stop_all_syncs, methods=["POST"]))
app.routes.append(Route("/api/get_user_access_menu/{username}", get_user_access_menu, methods=["GET"]))
app.routes.append(Route("/api/get_default_home_page/{username}", get_default_home_page, methods=["GET"]))
app.routes.append(Route("/api/set_default_home_page/{username}", set_default_home_page, methods=["POST"]))

async def project_root(request: Request):
    """
    Handler for GET /project (no trailing slash):
    1) If default_home_page is None or not in accessmenu_list → redirect to "/project/".
    2) Else → find menu_key by description and redirect to "/project/{menu_key}".
    """
    username = request.session.get("username")
    if not username:
        # Not logged in → show Admin index
        return RedirectResponse("/project/")

    result = fetch_user_menu_and_default(username)
    if result is None:
        # User not found or DB error → Admin index
        return RedirectResponse("/project/")

    menu_key, accessmenu_list, matches_description = result

    # If no valid menu_key → Admin index
    if menu_key is None:
        return RedirectResponse("/project/")

    # Otherwise, redirect to the resolved menu_key
    return RedirectResponse(f"/project/{menu_key}")

app.add_route("/project", project_root, methods=["GET"])

project = Admin(
    engine["DB2"],
    title="Warehouse Management",
    base_url="/project",
    statics_dir="api1/static",
    login_logo_url="/project/statics/logo_fcs.png",  # base_url + '/statics/' + path_to_the_file
    auth_provider=MyAuthProvider(allow_paths=["/statics/logo_fcs.png"]),
    middlewares=[Middleware(SessionMiddleware, secret_key=SECRET, max_age=7800)],
)
project.add_view(Items_tblView(Items_tbl, icon="fa fa-window-restore ", label="Items"))
project.add_view(Invoices_tblView(Invoices_tbl, icon="fa fa-tasks ", label="Copy"))
project.add_view_no_view(
    QuotationView(
        Quotation,
        icon="fa fa-arrow-circle-left",
        label="INVENTORY_1",
        identity="quotation",
    )
)
project.add_view(
    DropDown(
        "Quotations",
        icon="fa fa-sitemap",
        views=[
            Quotations_tbl_createView(
                Quotations1_tbl,
                icon="fa fa-sitemap",
                label="Create New",
            ),
            Quotations2_tbl_createView(
                Quotations2_tbl,
                icon="fa fa-eye",
                label="List",
            ),
        ],
    )
)
project.add_view(
    ListInvoicesView(
        Invoices2_tbl,
        icon="fa-solid fa-file-invoice",
        label="Invoices",
        identity="invoices2_tbl",
    ),
)
project.add_view_no_view(
    InvoicesDetailsView(
        InvoicesDetails_tbl,
        icon="fa-solid fa-file-invoice",
        label="Invoice Details",
        identity="InvoicesDetails_tbl",
    )
)
project.add_view(
    massupdateView(
        massupdate,
        icon="fa fa-spinner",
        label="Mass Update",
        identity="items_massupdate",
    )
)
project.add_view(
    ManualInventoryUpdateView(
        ManualInventoryUpdate,
        icon="fa fa-arrow-circle-right",
        label="Product Update",
        identity="manualinventoryupdate",
    )
)
project.add_view(
    DropDown(
        "Purchase Orders",
        icon="fa fa-sitemap",
        views=[
            PurchaseOrderView(
                PurchaseOrder,
                icon="fa fa-indent",
                label="Create New",
                identity="createpurchaseorder",
            ),
            PurchaseOrderView(
                PurchaseOrder,
                icon="fa fa-shield",
                label="List",
                identity="purchaseorder",
            ),
        ],
    )
)
project.add_view(
    OrdersLockView(
        OrdersLock,
        icon="fa fa-arrow-circle-up",
        label="Orders Lock",
        identity="orderslock",
    )
)
project.add_view(
    SettingsView(
        AdminUserProject_admin,  # FIXME: Mock-usage of the table, best way - to fix CustomViews and use them instead of this approach.
        icon="fa fa-cog",
        label="Settings",
        identity="settings",
    )
)
project.add_view(
    DropDown(
        "Reports",
        icon="fa fa-arrows",
        views=[
            Reports_createView(
                Reports,
                icon="fa fa-arrows-alt",
                label="Global Sales",
            ),
        ],
    )
)
project.add_view(
    Link(
        "ADMIN",
        url="/admin",
        icon="fa fa-link",
        identity="ADMIN",
        name="ADMIN",
    )
)


menu_dict = dict()
db_menu_dict = dict()
for i in project.__dict__["_models"]:
    label_menu = i.__dict__["label"]
    if label_menu == "INVENTORY_1":
        continue
    menu_dict[i.__dict__["identity"]] = i.__dict__["label"]
for i in project.__dict__["_views"]:
    if "url" in i.__dict__:
        menu_dict[i.__dict__["label"]] = i.__dict__["name"]
with Session(engine["DB_admin"]) as session:
    stmt_admin_menu = select(admin_menu_list.__table__.columns)
    rows_admin_menu = session.execute(stmt_admin_menu).mappings().all()
    db_menu_dict = dict(
        (rows_admin_menu[i]["menu"], rows_admin_menu[i]["id"])
        for i in range(len(rows_admin_menu))
    )
    add_menu_set = menu_dict.keys() - db_menu_dict.keys()
    del_menu_set = db_menu_dict.keys() - menu_dict.keys()
    for i in add_menu_set:
        query_add_menu = insert(admin_menu_list).values(
            menu=i,
            description=menu_dict[i],
        )
        answ_add_menu = session.execute(query_add_menu)
    for i in del_menu_set:
        stmt_del_menu = delete(admin_menu_list).where(
            admin_menu_list.id == db_menu_dict[i]
        )
        answ_del_menu = session.execute(stmt_del_menu)
    session.commit()
project.mount_to(app)
