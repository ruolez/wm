import uuid
from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    HttpUrl,
    IPvAnyAddress,
    validator,
    NegativeInt,
    NonNegativeInt,
    NonPositiveInt,
    PositiveInt,
    NegativeFloat,
    NonNegativeFloat,
    NonPositiveFloat,
    PositiveFloat,
)


class AdminUserProjectIn(BaseModel):
    full_name: str = Field(min_length=3)
    email: EmailStr

    @validator("full_name")
    def validate_full_name(cls, v: str):
        if " " not in v:
            raise ValueError("Full name must contain a space (ex. John Doe)")
        if v.count(" ") > 1:
            raise ValueError(
                "They must me only one space between the first name and last name (ex. John Doe)"
            )
        return v


class AdminDBsIn(BaseModel):
    ipAddress: IPvAnyAddress
