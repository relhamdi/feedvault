from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.links import ItemCategoryLink

if TYPE_CHECKING:
    from app.models.item import Item


class CategoryBase(SQLModel):
    name: str
    parent_id: int | None = Field(default=None, foreign_key="category.id")
    source_id: int | None = Field(default=None, foreign_key="source.id")


class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    items: list["Item"] = Relationship(
        back_populates="categories",
        link_model=ItemCategoryLink,
    )


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
