from abc import ABC, abstractmethod
from datetime import datetime

from sqlmodel import Session

from app.core.sources.models import NormalizedItem, RawItem, ScrapeJob, ScrapeMode


class BaseSource(ABC):
    """Abstract class common to all sources."""

    def __init__(self, feed_id: int, session: Session, params: dict | None = None):
        self.feed_id = feed_id
        self.session = session
        self.params = params or {}

    @abstractmethod
    def fetch(self, job: ScrapeJob) -> list[RawItem]:
        """Fetch raw data from the source."""
        ...

    @abstractmethod
    def map(self, raw: RawItem) -> NormalizedItem:
        """Transform a RawItem into a NormalizedItem."""
        ...

    def should_stop(self, item_date: datetime, job: ScrapeJob) -> bool:
        """
        Indicate whether incremental scraping should stop (when we reach items older than the last scrape).
        True when items preceding the last scraping are reached.
        Always returns False on first scrape (date_from is None).
        """
        if job.mode != ScrapeMode.INCREMENTAL or job.date_from is None:
            return False
        return item_date <= job.date_from

    def run(self, job: ScrapeJob) -> list[NormalizedItem]:
        """Orchestrate fetch + map + incremental stop."""
        raw_items = self.fetch(job)
        normalized = []
        for raw in raw_items:
            item = self.map(raw)
            if self.should_stop(item.source_updated_at, job):
                break
            normalized.append(item)
        return normalized
