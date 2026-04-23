from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import TimestampModel

if TYPE_CHECKING:
    from app.models.item import Item


class AuthorBase(SQLModel):
    external_id: str
    source_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("source.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    name: str
    url: str | None = None
    icon_url: str | None = None


class Author(AuthorBase, TimestampModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    items: list["Item"] = Relationship(back_populates="author")


class AuthorCreate(AuthorBase):
    pass


class AuthorRead(AuthorBase, TimestampModel):
    id: int
