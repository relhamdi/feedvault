from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel

from app.core.sources.models import ScrapeJobStatus, ScrapeMode, ScrapeTargetType


class ScrapeJobRecordBase(SQLModel):
    feed_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("feed.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    source_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("source.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    mode: ScrapeMode
    status: ScrapeJobStatus = ScrapeJobStatus.PENDING
    target_type: ScrapeTargetType | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    items_upserted: int = 0
    error_message: str | None = None
    last_external_id: str | None = None
    last_page: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScrapeJobRecord(ScrapeJobRecordBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ScrapeJobRecordRead(ScrapeJobRecordBase):
    id: int
