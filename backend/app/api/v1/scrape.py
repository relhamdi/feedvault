import importlib
from datetime import UTC, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.core.sources.base import BaseSource
from app.core.sources.models import (
    ScrapeJob,
    ScrapeMode,
    ScrapeResult,
    ScrapeTargetType,
)
from app.core.sources.registry import get_scraper_class, registered_slugs
from app.core.upsert import upsert_item
from app.database import get_session
from app.models.feed import Feed
from app.models.source import Source

router = APIRouter()

# Import and register all scrapers
importlib.import_module("app.sources")


class ScrapeRequest(BaseModel):
    feed_id: int
    mode: ScrapeMode = ScrapeMode.INCREMENTAL
    date_from: datetime | None = None
    date_to: datetime | None = None


def _make_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _get_scraper(source: Source, feed: Feed, session: Session) -> BaseSource:
    """Instantiate the correct scraper based on source slug."""
    assert feed.id is not None

    cls = get_scraper_class(source.slug)

    if cls is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No scraper registered for source '{source.slug}'. "
                f"Available sources: {registered_slugs() or 'None'}"
            ),
        )

    return cls(
        feed_id=feed.id,
        session=session,
        params=feed.params or {},
    )


@router.post("/", response_model=ScrapeResult)
def scrape(payload: ScrapeRequest, session: Session = Depends(get_session)):
    feed = session.get(Feed, payload.feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    assert feed.id is not None

    source = session.get(Source, feed.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    job = ScrapeJob(
        target_type=ScrapeTargetType.FEED,
        target_id=feed.id,
        mode=payload.mode,
        date_from=_make_aware(
            payload.date_from
            if payload.mode == ScrapeMode.RANGE
            else (
                feed.last_scraped_at if payload.mode == ScrapeMode.INCREMENTAL else None
            )
        ),
        date_to=_make_aware(
            payload.date_to if payload.mode == ScrapeMode.RANGE else None
        ),
    )

    scraper = _get_scraper(source, feed, session)
    normalized_items = scraper.run(job)

    item_ids = []
    for normalized in normalized_items:
        item = upsert_item(
            session=session,
            normalized=normalized,
            feed=feed,
            source_slug=source.slug,
        )
        assert item.id is not None
        item_ids.append(item.id)

    feed.last_scraped_at = datetime.now(UTC)
    session.add(feed)
    session.commit()

    return ScrapeResult(feed_id=feed.id, upserted=len(item_ids), item_ids=item_ids)
