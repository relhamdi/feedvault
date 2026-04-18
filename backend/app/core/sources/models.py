from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ScrapeMode(str, Enum):
    INCREMENTAL = "INCREMENTAL"
    RANGE = "RANGE"
    FULL = "FULL"


class ScrapeJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class ScrapeTargetType(str, Enum):
    SOURCE = "source"
    FEED = "feed"
    ITEM = "item"


class ScrapeJob(BaseModel):
    target_type: ScrapeTargetType
    target_id: int
    mode: ScrapeMode
    date_from: datetime | None = None
    date_to: datetime | None = None
    status: ScrapeJobStatus = ScrapeJobStatus.PENDING


class ScrapeResult(BaseModel):
    feed_id: int
    upserted: int
    item_ids: list[int]


class RawAuthor(BaseModel):
    external_id: str
    name: str
    url: str | None = None
    icon_url: str | None = None


class RawCategory(BaseModel):
    external_id: str
    name: str
    parent_external_id: str | None = None
    source_id: int | None = None


class RawMediaType(str, Enum):
    IMAGE = "image"
    FILE = "file"
    LINK = "link"
    CODE = "code"


class RawMedia(BaseModel):
    media_type: RawMediaType
    url: str
    label: str | None = None
    mime_type: str | None = None
    extra: str | None = None


class RawItem(BaseModel):
    """Raw data returned by fetch(), before mapping."""

    external_id: str
    data: dict[str, Any]


class NormalizedItem(BaseModel):
    """Data normalized after mapping, ready for upsert into the database."""

    external_id: str
    title: str
    url: str
    description: str | None = None
    summary: str | None = None
    thumbnail_url: str | None = None  # Remote URL, downloaded afterward
    thumbnail_sub_path: str | None = None  # Optional sub path for thumbnail storage
    tags: list[str] = []
    stats: dict[str, Any] = {}
    raw_extra: dict[str, Any] = {}
    meta: dict = {}
    is_nsfw: bool = False
    is_public: bool = True
    source_published_at: datetime
    source_updated_at: datetime

    author: RawAuthor | None = None
    categories: list[RawCategory] = []
    media: list[RawMedia] = []
