from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, Relationship, SQLModel

from app.core.sources.models import RawMediaType as MediaType

if TYPE_CHECKING:
    from app.models.item import Item


class ItemMediaBase(SQLModel):
    item_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("item.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
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
