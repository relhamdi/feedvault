from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import TimestampModel
from app.models.links import ItemCategoryLink

if TYPE_CHECKING:
    from app.models.item import Item


class CategoryBase(SQLModel):
    name: str
    parent_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            # If parent is deleted, then becomes the root
            ForeignKey("category.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    source_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("source.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )


class Category(CategoryBase, TimestampModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    items: list["Item"] = Relationship(
        back_populates="categories",
        link_model=ItemCategoryLink,
        sa_relationship_kwargs={"passive_deletes": True},
    )


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase, TimestampModel):
    id: int
