from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.base import TimestampModel
from app.models.links import ItemCategoryLink

if TYPE_CHECKING:
    from app.models.item import Item


class CategoryBase(SQLModel):
    name: str
    parent_id: int | None = Field(default=None, foreign_key="category.id")
    source_id: int | None = Field(default=None, foreign_key="source.id")


class Category(CategoryBase, TimestampModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    items: list["Item"] = Relationship(
        back_populates="categories",
        link_model=ItemCategoryLink,
    )


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase, TimestampModel):
    id: int
