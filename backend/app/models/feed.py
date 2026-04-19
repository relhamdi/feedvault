from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON
from sqlmodel import Column, Field, Relationship, SQLModel

from app.models.base import TimestampModel

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.source import Source


class FeedBase(SQLModel):
    name: str
    source_id: int = Field(foreign_key="source.id")
    url: str
    icon_path: str | None = None
    color: str | None = None
    default_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_active: bool = True
    last_scraped_at: datetime | None = None
    params: dict = Field(default_factory=dict, sa_column=Column(JSON))


class Feed(FeedBase, TimestampModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    source: "Source" = Relationship(back_populates="feeds")
    items: list["Item"] = Relationship(back_populates="feed")


class FeedCreate(FeedBase):
    pass


class FeedUpdate(SQLModel):
    name: str | None = None
    url: str | None = None
    icon_path: str | None = None
    color: str | None = None
    default_tags: list[str] | None = None
    is_active: bool | None = None
    params: dict | None = None


class FeedRead(FeedBase, TimestampModel):
    id: int
