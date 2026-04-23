from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class LogLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ScrapeLogBase(SQLModel):
    job_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("scrapejobrecord.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    feed_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("feed.id", ondelete="CASCADE"),
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
    level: LogLevel = LogLevel.INFO
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScrapeLog(ScrapeLogBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ScrapeLogRead(ScrapeLogBase):
    id: int
