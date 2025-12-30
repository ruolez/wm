from dataclasses import dataclass, field
from typing import Optional, Sequence
from urllib.parse import urlencode

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER
from starlette.types import ASGIApp
from starlette_admin.exceptions import LoginFailed
from starlette_admin.i18n import lazy_gettext as _


@dataclass
class AdminUser:
    username: str = field(default_factory=lambda: _("Administrator"))
    photo_url: Optional[str] = None


class AuthProvider:
    def __init__(
        self,
        login_path: str = "/login",
        logout_path: str = "/logout",
        allow_paths: Optional[Sequence[str]] = None,
    ) -> None:
        self.login_path = login_path
        self.logout_path = logout_path
        self.allow_paths = allow_paths

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        raise LoginFailed("Not Implemented")

    async def is_authenticated(self, request: Request) -> bool:
        return False

    def get_admin_user(self, request: Request) -> Optional[AdminUser]:
        return None  # pragma: no cover

    async def logout(self, request: Request, response: Response) -> Response:
        raise NotImplementedError()


active_user = list()


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        provider: AuthProvider,
        allow_paths: Optional[Sequence[str]] = None,
    ) -> None:
        super().__init__(app)
        self.provider = provider
        self.allow_paths = list(allow_paths) if allow_paths is not None else []
        self.allow_paths.extend(
            [
                self.provider.login_path,
                "/statics/css/tabler.min.css",
                "/statics/css/fontawesome.min.css",
                "/statics/js/vendor/jquery.min.js",
                "/statics/js/vendor/tabler.min.js",
                "/statics/js/vendor/js.cookie.min.js",
            ]
        )
        self.allow_paths.extend(
            self.provider.allow_paths if self.provider.allow_paths is not None else []
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:

        if request.scope["path"] not in self.allow_paths and not (
            await self.provider.is_authenticated(request)
        ):
            return RedirectResponse(
                "{url}?{query_params}".format(
                    url=request.url_for(request.app.state.ROUTE_NAME + ":login"),
                    query_params=urlencode({"next": str(request.url)}),
                ),
                status_code=HTTP_303_SEE_OTHER,
            )
        return await call_next(request)
