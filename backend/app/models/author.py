from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.item import Item


class AuthorBase(SQLModel):
    external_id: str
    source_id: int = Field(foreign_key="source.id")
    name: str
    url: str | None = None
    icon_url: str | None = None


class Author(AuthorBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    items: list["Item"] = Relationship(back_populates="author")


class AuthorCreate(AuthorBase):
    pass


class AuthorRead(AuthorBase):
    id: int
    created_at: datetime
    updated_at: datetime
