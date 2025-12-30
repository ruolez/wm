import uuid
from datetime import datetime
from typing import Optional, Union

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


class Items_tblIn(BaseModel):


    CateID: Union[int, float]
    SubCateID: Union[int, float]
    UnitCost: Union[int, float]
    UnitPrice: Union[int, float]
    ItemWeight: str



class PostIn(BaseModel):
    id: Optional[int]
    title: str = Field(min_length=3)
    text: str = Field(min_length=5)
    date: datetime


