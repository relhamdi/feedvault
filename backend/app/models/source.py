from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.feed import Feed


class SourceType(str, Enum):
    RSS = "RSS"
    API = "API"
    SCRAPER = "SCRAPER"


class SourceBase(SQLModel):
    slug: str = Field(unique=True, index=True)
    name: str
    color: str | None = None
    icon_path: str | None = None
    source_type: SourceType
    base_url: str
    default_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_active: bool = True
    last_scraped_at: datetime | None = None


class Source(SourceBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    credentials: bytes | None = None

    feeds: list["Feed"] = Relationship(back_populates="source")


class SourceCreate(SourceBase):
    pass


class SourceUpdate(SQLModel):
    name: str | None = None
    color: str | None = None
    icon_path: str | None = None
    source_type: SourceType | None = None
    base_url: str | None = None
    default_tags: list[str] | None = None
    is_active: bool | None = None


class SourceRead(SourceBase):
    id: int
    created_at: datetime
    updated_at: datetime
