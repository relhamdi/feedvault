from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class ItemCategoryLink(SQLModel, table=True):
    item_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("item.id", ondelete="CASCADE"),
            nullable=True,
            primary_key=True,
        ),
    )
    category_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("category.id", ondelete="CASCADE"),
            nullable=True,
            primary_key=True,
        ),
    )
