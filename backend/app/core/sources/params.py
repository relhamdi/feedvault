from enum import Enum
from typing import Any

from pydantic import BaseModel


class ParamType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    TEXTAREA = "textarea"
    BOOL = "bool"


class SelectOption(BaseModel):
    value: str
    label: str


class ParamField(BaseModel):
    description: str
    type: ParamType = ParamType.TEXT
    default: Any = None
    options: list[SelectOption] = []
    min: int | None = None
    max: int | None = None
