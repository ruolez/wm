from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqla.exceptions import NotSupportedValue
from starlette_admin.fields import FileField as BaseFileField
from starlette_admin.fields import ImageField as BaseImageField


@dataclass
class FileField(BaseFileField):
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        try:
            return _serialize_sqlalchemy_file_library(
                request, value, action, self.multiple
            )
        except (
            ImportError,
            ModuleNotFoundError,
            NotSupportedValue,
        ):
            return super().serialize_value(request, value, action)


@dataclass
class ImageField(BaseImageField):
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        try:
            return _serialize_sqlalchemy_file_library(
                request, value, action, self.multiple
            )
        except (
            ImportError,
            ModuleNotFoundError,
            NotSupportedValue,
        ):
            return super().serialize_value(request, value, action)


def _serialize_sqlalchemy_file_library(
    request: Request, value: Any, action: RequestAction, is_multiple: bool
) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]:
    from sqlalchemy_file import File
    if isinstance(value, File) or (
        isinstance(value, list) and all(isinstance(f, File) for f in value)
    ):
        data = []
        for item in value if isinstance(value, list) else [value]:
            path = item["path"]
            if (
                action == RequestAction.LIST
                and getattr(item, "thumbnail", None) is not None
            ):
                path = item["thumbnail"]["path"]
            storage, file_id = path.split("/")
            data.append(
                {
                    "content_type": item["content_type"],
                    "filename": item["filename"],
                    "url": str(
                        request.url_for(
                            request.app.state.ROUTE_NAME + ":api:file",
                            storage=storage,
                            file_id=file_id,
                        )
                    ),
                }
            )
        return data if is_multiple else data[0]
    raise NotSupportedValue
