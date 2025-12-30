import inspect
from abc import abstractmethod
import copy
from urllib.parse import urlsplit, parse_qsl
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from jinja2 import Template
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin._types import ExportType, RequestAction
from starlette_admin.actions import action
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import (
    BaseField,
    CollectionField,
    FileField,
    HasOne,
    RelationField,
)
from starlette_admin.helpers import extract_fields
from starlette_admin.i18n import get_locale, ngettext
from starlette_admin.i18n import lazy_gettext as _
from sqlalchemy.orm import Session

from api1 import (
    engine,
    engine_nick,
    engine_nick_name,
    SEARCH_IN_DICT_VALUE_RETURN_KEY,
    engine_name_db,
    engine_name_nick,
)
from sqlalchemy import (
    insert,
    select,
    update,
    delete,
    text,
    func,
)


from api1.users.model import (
    AdminUserProject_admin,
    Items_tbl,
    Quotations_tbl,
    QuotationsDetails_tbl,
    QuotationsInProgress,
    QuotationsStatus,
    Shippers_tbl,
    admin_menu_list,
)


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


class BaseView:
    label: str = ""
    icon: Optional[str] = None

    def is_active(self, request: Request) -> bool:
        """Return true if the current view is active"""
        return False

    def is_accessible(self, request: Request) -> bool:
        """
        Override this method to add permission checks.
        Return True if current user can access this view
        """
        return True


class DropDown(BaseView):
    """
    Group views inside a dropdown

    Example:
        ```Python
        admin.add_view(
            DropDown(
                "Resources",
                icon="fa fa-list",
                views=[
                    ModelView(User),
                    Link(label="Home Page", url="/"),
                    CustomView(label="Dashboard", path="/dashboard", template_path="dashboard.html"),
                ],
            )
        )
        ```
    """

    def __init__(
        self,
        label: str,
        views: List[Union[Type[BaseView], BaseView]],
        icon: Optional[str] = None,
        always_open: bool = True,
    ) -> None:
        self.label = label
        self.icon = icon
        self.always_open = always_open
        self.views: List[BaseView] = [
            (v if isinstance(v, BaseView) else v()) for v in views
        ]

    def is_active(self, request: Request) -> bool:
        return any(v.is_active(request) for v in self.views)

    def is_accessible(self, request: Request) -> bool:
        return any(v.is_accessible(request) for v in self.views)


class Link(BaseView):
    """
    Add arbitrary hyperlinks to the menu

    Example:
        ```Python
        admin.add_view(Link(label="Home Page", icon="fa fa-link", url="/"))
        ```
    """

    def __init__(
        self,
        label: str = "",
        icon: Optional[str] = None,
        identity: Optional[str] = None,
        name: Optional[str] = None,
        url: str = "/",
        target: Optional[str] = "_self",
    ):
        self.label = label
        self.icon = icon
        self.url = url
        self.target = target
        self.identity = identity
        self.name = name


class CustomView(BaseView):
    """
    Add your own views (not tied to any particular model). For example,
    a custom home page that displays some analytics data.

    Attributes:
        path: Route path
        template_path: Path to template file
        methods: HTTP methods
        name: Route name
        add_to_menu: Display to menu or not

    Example:
        ```Python
        admin.add_view(CustomView(label="Home", icon="fa fa-home", path="/home", template_path="home.html"))
        ```
    """

    def __init__(
        self,
        label: str,
        icon: Optional[str] = None,
        path: str = "/",
        template_path: str = "index.html",
        name: Optional[str] = None,
        methods: Optional[List[str]] = None,
        add_to_menu: bool = True,
    ):
        self.label = label
        self.icon = icon
        self.path = path
        self.template_path = template_path
        self.name = name
        self.methods = methods
        self.add_to_menu = add_to_menu

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        """Default methods to render view. Override this methods to add your custom logic."""
        return templates.TemplateResponse(
            self.template_path,
            {
                "request": request,
                "menu": menu(request),
            },
        )

    def is_active(self, request: Request) -> bool:
        return request.scope["path"] == self.path


class BaseModelView(BaseView):

    identity: Optional[str] = None
    name: Optional[str] = None
    fields: Sequence[BaseField] = []
    pk_attr: Optional[str] = None
    form_include_pk: bool = False
    exclude_fields_from_list: Sequence[str] = []
    exclude_fields_from_detail: Sequence[str] = []
    exclude_fields_from_create: Sequence[str] = []
    exclude_fields_from_edit: Sequence[str] = []
    searchable_fields: Optional[Sequence[str]] = None
    sortable_fields: Optional[Sequence[str]] = None
    fields_default_sort: Optional[Sequence[Union[Tuple[str, bool], str]]] = None
    export_types: Sequence[ExportType] = [
        ExportType.CSV,
        ExportType.EXCEL,
        ExportType.PRINT,
    ]
    export_fields: Optional[Sequence[str]] = None
    column_visibility: bool = True
    search_builder: bool = True
    page_size: int = 10
    page_size_options: Sequence[int] = [10, 25, 50, 100]
    responsive_table: bool = False
    list_template: str = "list.html"
    detail_template: str = "detail.html"
    create_template: str = "create.html"
    edit_template: str = "edit.html"
    actions: Optional[Sequence[str]] = None

    _find_foreign_model: Callable[[str], "BaseModelView"]

    def __init__(self) -> None:  # noqa: C901
        fringe = list(self.fields)
        all_field_names = []
        while len(fringe) > 0:
            field = fringe.pop(0)
            if not hasattr(field, "_name"):
                field._name = field.name  # type: ignore
            if isinstance(field, CollectionField):
                for f in field.fields:
                    f._name = f"{field._name}.{f.name}"  # type: ignore
                fringe.extend(field.fields)
            name = field._name  # type: ignore
            if name == self.pk_attr and not self.form_include_pk:
                field.exclude_from_create = True
                field.exclude_from_edit = True
            if name in self.exclude_fields_from_list:
                field.exclude_from_list = True
            if name in self.exclude_fields_from_detail:
                field.exclude_from_detail = True
            if name in self.exclude_fields_from_create:
                field.exclude_from_create = True
            if name in self.exclude_fields_from_edit:
                field.exclude_from_edit = True
            if not isinstance(field, CollectionField):
                all_field_names.append(name)
                field.searchable = (self.searchable_fields is None) or (
                    name in self.searchable_fields
                )
                field.orderable = (self.sortable_fields is None) or (
                    name in self.sortable_fields
                )
        if self.searchable_fields is None:
            self.searchable_fields = all_field_names[:]
        if self.sortable_fields is None:
            self.sortable_fields = all_field_names[:]
        if self.export_fields is None:
            self.export_fields = all_field_names[:]
        if self.fields_default_sort is None:
            self.fields_default_sort = [self.pk_attr]  # type: ignore[list-item]

        self._actions: Dict[str, Dict[str, str]] = {}
        self._handlers: Dict[str, Callable[[Request, Sequence[Any]], Awaitable]] = {}
        self._init_actions()

    def is_active(self, request: Request) -> bool:
        return request.path_params.get("identity", None) == self.identity

    def _init_actions(self) -> None:
        for _method_name, method in inspect.getmembers(
            self, predicate=inspect.ismethod
        ):
            if hasattr(method, "_action"):
                name = method._action.get("name")
                self._actions[name] = method._action
                self._handlers[name] = method
        if self.actions is None:
            self.actions = list(self._handlers.keys())
        for action_name in self.actions:
            if action_name not in self._actions:
                raise ValueError(f"Unknown action with name `{action_name}`")

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "delete":
            return self.can_delete(request)
        return True

    async def get_all_actions(self, request: Request) -> List[Optional[dict]]:
        actions = []
        assert self.actions is not None
        for action_name in self.actions:
            if await self.is_action_allowed(request, action_name):
                actions.append(self._actions.get(action_name))
        return actions

    async def handle_action(
        self, request: Request, pks: List[Any], name: str
    ) -> Union[str, Response]:
        """
        Handle action with `name`.
        Raises:
            ActionFailed: to display meaningfully error
        """
        handler = self._handlers.get(name, None)
        if handler is None:
            raise ActionFailed("Invalid action")
        if not await self.is_action_allowed(request, name):
            raise ActionFailed("Forbidden")
        handler_return = await handler(request, pks)
        custom_response = self._actions[name]["custom_response"]
        if isinstance(handler_return, Response) and not custom_response:
            raise ActionFailed(
                "Set custom_response to true, to be able to return custom response"
            )
        return handler_return

    @action(
        name="delete",
        text=_("Delete"),
        confirmation=_("Are you sure you want to delete selected items?"),
        submit_btn_text=_("Yes, delete all"),
        submit_btn_class="btn-danger",
    )
    async def delete_action(self, request: Request, pks: List[Any]) -> str:
        affected_rows = await self.delete(request, pks)
        return ngettext(
            "Item was successfully deleted",
            "%(count)d items were successfully deleted",
            affected_rows or 0,
        ) % {"count": affected_rows}

    @abstractmethod
    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        raise NotImplementedError()

    @abstractmethod
    async def count(
        self,
        request: Request,
        where: Union[Dict[str, Any], str, None] = None,
    ) -> int:
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        raise NotImplementedError()

    @abstractmethod
    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        raise NotImplementedError()

    @abstractmethod
    async def find_by_pks(self, request: Request, pks: List[Any]) -> Sequence[Any]:
        raise NotImplementedError()

    @abstractmethod
    async def create(self, request: Request, data: Dict) -> Any:
        raise NotImplementedError()

    @abstractmethod
    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        raise NotImplementedError()

    def can_view_details(self, request: Request) -> bool:
        return True

    def can_create(self, request: Request) -> bool:
        return True

    def can_edit(self, request: Request) -> bool:
        return True

    def can_delete(self, request: Request) -> bool:
        return True

    @staticmethod
    def _chunk_list(lst: List[Any], chunk_size: int = 2000):
        """Helper function to chunk a list into smaller lists of a given size."""
        for i in range(0, len(lst), chunk_size):
            yield lst[i: i + chunk_size]

    # _get_status_data method removed - status is now fetched in SQL query with cross-database JOIN

    @staticmethod
    def _get_profit_margin_data(dbname: str, quotation_ids: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Retrieve profit calculation data and auto order information for given QuotationIDs from the specified database."""
        profit_data = {}
        auto_order_data = {}

        with Session(engine[engine_name_db[dbname]]) as session:
            all_profit_results = []
            for chunk in BaseModelView._chunk_list(quotation_ids, 500):
                stmt_profit = (
                    select(
                        QuotationsDetails_tbl.QuotationID,
                        func.sum(QuotationsDetails_tbl.UnitCost * QuotationsDetails_tbl.Qty).label("TotalCost"),
                        func.sum(QuotationsDetails_tbl.UnitPrice * QuotationsDetails_tbl.Qty).label("TotalPrice"),
                    )
                    .where(QuotationsDetails_tbl.QuotationID.in_(chunk))
                    .group_by(QuotationsDetails_tbl.QuotationID)
                )
                results = session.execute(stmt_profit).mappings().all()
                all_profit_results.extend(results)
            if all_profit_results:
                profit_data = {str(row["QuotationID"]): row for row in all_profit_results}

            # Check of AutoOrderNo for correcting status value.
            # AutoOrderNo != Null -> Converted value.
            all_auto_order_results = []
            for chunk in BaseModelView._chunk_list(quotation_ids, 500):
                stmt_auto_order = (
                    select(
                        Quotations_tbl.QuotationID,
                        Quotations_tbl.AutoOrderNo,
                    ).where(Quotations_tbl.QuotationID.in_(chunk))
                )
                results = session.execute(stmt_auto_order).mappings().all()
                all_auto_order_results.extend(results)
            if all_auto_order_results:
                auto_order_data = {str(row["QuotationID"]): row["AutoOrderNo"] for row in all_auto_order_results}

        return profit_data, auto_order_data

    @staticmethod
    def bulk_load_additional_quotation_data(items: List[Dict[str, Any]]):
        """
        Enrich quotation items with additional data.
        Note: StatusQuotation and ProfitMargin are now included in the SQL query, so no enrichment needed.
        This function is kept for potential future enrichment needs.
        """
        if not items:
            return

        # StatusQuotation is already set from SQL query - no need to modify it
        # ProfitMargin is already calculated in SQL query - no need to recalculate it
        # This function is now a no-op but kept for backward compatibility
        pass

    async def serialize_field_value(
        self, value: Any, field: BaseField, action: RequestAction, request: Request
    ) -> Any:
        if value is None:
            return await field.serialize_none_value(request, action)
        return await field.serialize_value(request, value, action)

    async def serialize(
        self,
        obj: Any,
        request: Request,
        action: RequestAction,
        include_relationships: bool = True,
        include_select2: bool = False,
        DBD: str = "",
        QuotationID: str = "",
    ) -> Dict[str, Any]:
        obj_serialized: Dict[str, Any] = {}
        user_account_status = request.state.user["statususer"].strip().lower()

        for field in self.fields:
            if field.name in ["ProfitMargin", "StatusQuotation"]:
                continue

            if isinstance(field, RelationField) and include_relationships:
                # Handle both dict-like/Mapping objects (including RowMapping) and ORM objects
                if isinstance(obj, Mapping):
                    value = obj.get(field.name)
                else:
                    value = getattr(obj, field.name, None)
                foreign_model = self._find_foreign_model(field.identity)
                assert foreign_model.pk_attr is not None
                if value is None:
                    obj_serialized[field.name] = None
                elif isinstance(field, HasOne):
                    obj_serialized[field.name] = (
                        getattr(value, foreign_model.pk_attr)
                        if action == RequestAction.EDIT
                        else await foreign_model.serialize(value, request, action, include_relationships=False)
                    )
                else:
                    obj_serialized[field.name] = (
                        [getattr(v, foreign_model.pk_attr) for v in value]
                        if action == RequestAction.EDIT
                        else [
                            await foreign_model.serialize(v, request, action, include_relationships=False)
                            for v in value
                        ]
                    )
            elif not isinstance(field, RelationField):
                value = await field.parse_obj(request, obj)
                obj_serialized[field.name] = await self.serialize_field_value(value, field, action, request)

        assert self.pk_attr is not None
        route_name = request.app.state.ROUTE_NAME
        # Handle both dict-like/Mapping objects (including RowMapping) and ORM objects
        if isinstance(obj, Mapping):
            pk_value = obj.get(self.pk_attr)
        else:
            pk_value = getattr(obj, self.pk_attr, None)
        obj_serialized[self.pk_attr] = obj_serialized.get(self.pk_attr, str(pk_value) if pk_value is not None else None)

        if "DBname" in obj:
            obj_serialized["DBname"] = obj["DBname"]
        if "ProfitMargin" in obj:
            obj_serialized["ProfitMargin"] = obj["ProfitMargin"]
        if "StatusQuotation" in obj:
            obj_serialized["StatusQuotation"] = obj["StatusQuotation"]
        if "QuotationID" in obj:
            obj_serialized["QuotationID"] = obj["QuotationID"]
            obj_serialized["_print_quotation"] = str(
                request.url_for(route_name + ":print_quotation", identity=self.identity)
            )
            obj_serialized["_view_edit_quotation_1"] = str(
                request.url_for(route_name + ":list", identity="quotations3_tbl")
            )
        if "InvoiceID" in obj:
            obj_serialized["_view_invoice_details"] = str(
                request.url_for(f"{route_name}:list", identity="InvoicesDetails_tbl")
            )

        return obj_serialized



    async def repr(self, obj: Any, request: Request) -> str:
        repr_method = getattr(
            obj,
            "__admin_repr__",
            lambda request: str(getattr(obj, self.pk_attr)),  # type: ignore[arg-type]
        )
        if inspect.iscoroutinefunction(repr_method):
            return await repr_method(request)
        return repr_method(request)

    async def select2_result(self, obj: Any, request: Request) -> str:
        template_str = (
            "<span>{%for col in fields %}{%if obj[col]%}<strong>{{col}}:"
            " </strong>{{obj[col]}} {%endif%}{%endfor%}</span>"
        )
        fields = [
            field.name
            for field in self.fields
            if (
                not isinstance(field, (RelationField, FileField))
                and not field.exclude_from_detail
            )
        ]
        html_repr_method = getattr(
            obj,
            "__admin_select2_repr__",
            lambda request: Template(template_str, autoescape=True).render(
                obj=obj, fields=fields
            ),
        )
        if inspect.iscoroutinefunction(html_repr_method):
            return await html_repr_method(request)
        return html_repr_method(request)

    async def select2_selection(self, obj: Any, request: Request) -> str:
        return await self.select2_result(obj, request)

    def _length_menu(self) -> Any:
        return [
            self.page_size_options,
            [(_("All") if i < 0 else i) for i in self.page_size_options],
        ]

    def _search_columns_selector(self) -> List[str]:
        return ["%s:name" % name for name in self.searchable_fields]  # type: ignore

    def _export_columns_selector(self) -> List[str]:
        return ["%s:name" % name for name in self.export_fields]  # type: ignore

    def get_fields_list(
        self,
        request: Request,
        action: RequestAction = RequestAction.LIST,
    ) -> Sequence[BaseField]:
        """Return a list of field instances to display in the specified view action.
        This function excludes fields with corresponding exclude flags, which are
        determined by the `exclude_fields_from_*` attributes.

        Parameters:
             request: The request being processed.
             action: The type of action being performed on the view.
        """
        return extract_fields(self.fields, action)

    def _additional_css_links(
        self, request: Request, action: RequestAction
    ) -> Sequence[str]:
        links = []
        for field in self.fields:
            if (
                (action == RequestAction.LIST and field.exclude_from_list)
                or (action == RequestAction.DETAIL and field.exclude_from_detail)
                or (action == RequestAction.CREATE and field.exclude_from_create)
                or (action == RequestAction.EDIT and field.exclude_from_edit)
            ):
                continue
            for link in field.additional_css_links(request, action) or []:
                if link not in links:
                    links.append(link)
        return links

    def _additional_js_links(
        self, request: Request, action: RequestAction
    ) -> Sequence[str]:
        links = []
        for field in self.fields:
            if (action == RequestAction.CREATE and field.exclude_from_create) or (
                action == RequestAction.EDIT and field.exclude_from_edit
            ):
                continue
            for link in field.additional_js_links(request, action) or []:
                if link not in links:
                    links.append(link)
        return links

    async def _configs(
        self, request: Request, dop: Dict[str, str] = None
    ) -> Dict[str, Any]:
        locale = get_locale()

        return {
            "label": self.label,
            "pageSize": self.page_size,
            "lengthMenu": self._length_menu(),
            "searchColumns": self._search_columns_selector(),
            "exportColumns": self._export_columns_selector(),
            "fieldsDefaultSort": dict(
                (it, False) if isinstance(it, str) else it
                for it in self.fields_default_sort  # type: ignore[union-attr]
            ),
            "exportTypes": self.export_types,
            "columnVisibility": self.column_visibility,
            "searchBuilder": self.search_builder,
            "responsiveTable": self.responsive_table,
            "fields": [f.dict() for f in self.get_fields_list(request)],
            "actions": await self.get_all_actions(request),
            "pk": self.pk_attr,
            "locale": locale,
            "apiUrl": request.url_for(
                f"{request.app.state.ROUTE_NAME}:api", identity=self.identity
            ),
            "actionUrl": request.url_for(
                f"{request.app.state.ROUTE_NAME}:action", identity=self.identity
            ),
            "dt_i18n_url": request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics", path=f"i18n/dt/{locale}.json"
            ),
            "referer": request.scope["headers"],
            "dop": dop,
        }
