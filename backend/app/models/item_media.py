from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.item import Item


class MediaType(str, Enum):
    IMAGE = "image"
    FILE = "file"
    LINK = "link"
    CODE = "code"


class ItemMediaBase(SQLModel):
    item_id: int = Field(foreign_key="item.id")
    media_type: MediaType
    url: str
    label: str | None = None
    mime_type: str | None = None
    extra: str | None = None


class ItemMedia(ItemMediaBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    item: "Item" = Relationship(back_populates="media")


class ItemMediaCreate(ItemMediaBase):
    pass


class ItemMediaRead(ItemMediaBase):
    id: int
    created_at: datetime
