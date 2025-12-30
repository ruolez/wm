from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette_admin.contrib.sqla.view import ModelView as BaseModelView
from starlette_admin.helpers import pydantic_error_to_form_validation_errors


class ModelView(BaseModelView):

    def __init__(
        self,
        model: Type[Any],
        pydantic_model: Type[BaseModel],
        icon: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        identity: Optional[str] = None,
    ):
        self.pydantic_model = pydantic_model
        super().__init__(model, icon, name, label, identity)

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        try:
            self.pydantic_model(**data)
        except ValidationError as error:
            raise pydantic_error_to_form_validation_errors(error) from error
