from datetime import UTC, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class LogLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ScrapeLogBase(SQLModel):
    job_id: int = Field(foreign_key="scrapejobrecord.id")
    feed_id: int | None = Field(default=None, foreign_key="feed.id")
    source_id: int | None = Field(default=None, foreign_key="source.id")
    level: LogLevel = LogLevel.INFO
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScrapeLog(ScrapeLogBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ScrapeLogRead(ScrapeLogBase):
    id: int
