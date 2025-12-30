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
class AdminDBsIn(BaseModel):
    ipAddress: IPvAnyAddress
