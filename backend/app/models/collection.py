from enum import Enum

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel

from app.models.base import TimestampModel


class FilterOperator(str, Enum):
    AND = "AND"
    OR = "OR"


class CollectionBase(SQLModel):
    name: str
    color: str | None = None
    filter_source_ids: list[int] | None = Field(default=None, sa_column=Column(JSON))
    filter_feed_ids: list[int] | None = Field(default=None, sa_column=Column(JSON))
    filter_tags: list[str] | None = Field(default=None, sa_column=Column(JSON))
    filter_operator: FilterOperator = FilterOperator.OR


class Collection(CollectionBase, TimestampModel, table=True):
    id: int | None = Field(default=None, primary_key=True)


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(SQLModel):
    name: str | None = None
    color: str | None = None
    filter_source_ids: list[int] | None = None
    filter_feed_ids: list[int] | None = None
    filter_tags: list[str] | None = None
    filter_operator: FilterOperator | None = None


class CollectionRead(CollectionBase, TimestampModel):
    id: int
