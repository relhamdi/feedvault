from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON
from sqlmodel import Column, Field, Relationship, SQLModel

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


class Feed(FeedBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

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


class FeedRead(FeedBase):
    id: int
    created_at: datetime
    updated_at: datetime
