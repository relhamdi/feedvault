from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer
from sqlmodel import Column, Field, Relationship, SQLModel

from app.models.author import AuthorRead
from app.models.base import TimestampModel
from app.models.category import CategoryRead
from app.models.item_media import ItemMediaRead
from app.models.links import ItemCategoryLink

if TYPE_CHECKING:
    from app.models.author import Author
    from app.models.category import Category
    from app.models.feed import Feed
    from app.models.item_media import ItemMedia


class ItemBase(SQLModel):
    feed_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("feed.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    external_id: str = Field(index=True)
    title: str
    url: str
    description: str | None = None
    summary: str | None = None
    thumbnail_path: str | None = None
    thumbnail_url: str | None = None
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    stats: dict = Field(default_factory=dict, sa_column=Column(JSON))
    raw_extra: dict = Field(default_factory=dict, sa_column=Column(JSON))
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON))
    is_read: bool = False
    is_favorite: bool = False
    is_nsfw: bool = False
    is_public: bool = True
    source_published_at: datetime
    source_updated_at: datetime
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Item(ItemBase, TimestampModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    author_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("author.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    feed: "Feed" = Relationship(back_populates="items")
    author: "Author" = Relationship(back_populates="items")
    categories: list["Category"] = Relationship(
        back_populates="items",
        link_model=ItemCategoryLink,
        sa_relationship_kwargs={"passive_deletes": True},
    )
    media: list["ItemMedia"] = Relationship(
        back_populates="item",
        sa_relationship_kwargs={"passive_deletes": True},
    )


class ItemCreate(ItemBase):
    author_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("author.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


class ItemUpdate(SQLModel):
    is_read: bool | None = None
    is_favorite: bool | None = None
    is_nsfw: bool | None = None
    is_public: bool | None = None
    tags: list[str] | None = None
    meta: dict | None = None


class ItemRead(ItemBase, TimestampModel):
    id: int
    author: AuthorRead | None = None
    media: list[ItemMediaRead] = []
    categories: list[CategoryRead] = []
