import importlib
from datetime import UTC, datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, col, func, select

from app.core.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.core.crud import get_or_404, paginate
from app.core.sources.base import BaseSource
from app.core.sources.models import (
    ScrapeJob,
    ScrapeJobStatus,
    ScrapeMode,
    ScrapeTargetType,
)
from app.core.sources.registry import get_scraper_class, registered_slugs
from app.core.upsert import upsert_item
from app.database import engine, get_session
from app.models.feed import Feed
from app.models.pagination import PaginatedResponse
from app.models.scrape_job import ScrapeJobRecord, ScrapeJobRecordRead
from app.models.scrape_log import LogLevel, ScrapeLog, ScrapeLogRead
from app.models.source import Source

router = APIRouter()

# Import and register all scrapers
importlib.import_module("app.sources")


class ScrapeRequest(BaseModel):
    feed_id: int
    mode: ScrapeMode = ScrapeMode.INCREMENTAL
    date_from: datetime | None = None
    date_to: datetime | None = None
    external_ids: list[str] | None = None


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
        source=source,
        params=feed.params or {},
    )


def _update_source_last_scraped(session: Session, source_id: int) -> None:
    """Set source.last_scraped_at to the oldest feed.last_scraped_at among active feeds."""
    result = session.exec(
        select(func.min(Feed.last_scraped_at))
        .where(Feed.source_id == source_id)
        .where(Feed.is_active)
    ).first()

    source = session.get(Source, source_id)
    if source and result:
        source.last_scraped_at = _make_aware(result)
        session.add(source)
        session.commit()


def _log(
    session: Session,
    job_id: int,
    feed_id: int,
    source_id: int,
    level: LogLevel,
    message: str,
) -> None:
    """Persist a scrape log entry."""
    session.add(
        ScrapeLog(
            job_id=job_id,
            feed_id=feed_id,
            source_id=source_id,
            level=level,
            message=message,
        )
    )
    session.commit()


def _run_scrape(job_record_id: int, payload: ScrapeRequest) -> None:
    """Background task: runs the full scraping pipeline for a feed."""

    with Session(engine) as session:
        job_record = session.get(ScrapeJobRecord, job_record_id)
        if not job_record:
            return
        assert job_record.id is not None

        feed = session.get(Feed, payload.feed_id)
        if not feed:
            job_record.status = ScrapeJobStatus.ERROR
            job_record.error_message = f"Feed {payload.feed_id} not found"
            session.add(job_record)
            session.commit()
            return
        assert feed.id is not None

        source = session.get(Source, feed.source_id)
        if not source:
            job_record.status = ScrapeJobStatus.ERROR
            job_record.error_message = f"Source {feed.source_id} not found"
            session.add(job_record)
            session.commit()
            return
        assert source.id is not None

        # Mark job as running
        job_record.status = ScrapeJobStatus.RUNNING
        job_record.started_at = datetime.now(UTC)
        session.add(job_record)
        session.commit()

        _log(
            session,
            job_record.id,
            feed.id,
            source.id,
            LogLevel.INFO,
            f"Scraping started — feed '{feed.name}' mode={payload.mode}",
        )

        try:
            job = ScrapeJob(
                target_type=ScrapeTargetType.FEED,
                target_id=feed.id,
                mode=payload.mode,
                date_from=_make_aware(
                    payload.date_from
                    if payload.mode == ScrapeMode.RANGE
                    else (
                        feed.last_scraped_at
                        if payload.mode == ScrapeMode.INCREMENTAL
                        else None
                    )
                ),
                date_to=_make_aware(
                    payload.date_to if payload.mode == ScrapeMode.RANGE else None
                ),
            )

            scraper = _get_scraper(source, feed, session)

            if payload.external_ids:
                # Fetch by IDs mode — bypass normal fetch/run pipeline
                job.target_type = ScrapeTargetType.ITEM

                try:
                    raw_items = scraper.fetch_by_ids(payload.external_ids)
                except NotImplementedError as e:
                    raise ValueError(
                        f"Source '{source.slug}' does not support fetch_by_ids"
                    ) from e

                normalized_items = [scraper.map(r) for r in raw_items]
                _log(
                    session,
                    job_record.id,
                    feed.id,
                    source.id,
                    LogLevel.INFO,
                    f"Fetching {len(payload.external_ids)} item(s) by ID",
                )
            else:
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
                job_record.last_external_id = normalized.external_id
                session.add(job_record)
                session.commit()

            feed.last_scraped_at = datetime.now(UTC)
            session.add(feed)
            session.commit()

            _update_source_last_scraped(session, feed.source_id)

            job_record.status = ScrapeJobStatus.DONE
            job_record.finished_at = datetime.now(UTC)
            job_record.items_upserted = len(item_ids)
            session.add(job_record)
            session.commit()

            _log(
                session,
                job_record.id,
                feed.id,
                source.id,
                LogLevel.INFO,
                f"Scraping done — {len(item_ids)} items upserted",
            )

        except Exception as e:
            job_record.status = ScrapeJobStatus.ERROR
            job_record.finished_at = datetime.now(UTC)
            job_record.error_message = str(e)
            session.add(job_record)
            session.commit()

            _log(
                session,
                job_record.id,
                feed.id,
                source.id,
                LogLevel.ERROR,
                f"Scraping failed — {e}",
            )


@router.post("/", response_model=ScrapeJobRecordRead, status_code=202)
def scrape(
    payload: ScrapeRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """Start a scraping job. Returns immediately with job details."""
    feed = get_or_404(session, Feed, payload.feed_id)
    assert feed.id is not None
    source = get_or_404(session, Source, feed.source_id)
    assert source.id is not None

    # Reject if a job is already running for this feed
    running = session.exec(
        select(ScrapeJobRecord)
        .where(ScrapeJobRecord.feed_id == payload.feed_id)
        .where(ScrapeJobRecord.status == ScrapeJobStatus.RUNNING)
    ).first()
    if running:
        raise HTTPException(
            status_code=409,
            detail=f"A scraping job is already running for feed {payload.feed_id}",
        )

    job_record = ScrapeJobRecord(
        feed_id=feed.id,
        source_id=source.id,
        mode=payload.mode,
        status=ScrapeJobStatus.PENDING,
    )
    session.add(job_record)
    session.commit()
    session.refresh(job_record)
    assert job_record.id is not None

    background_tasks.add_task(_run_scrape, job_record.id, payload)
    return job_record


@router.get("/jobs", response_model=PaginatedResponse[ScrapeJobRecordRead])
def list_jobs(
    feed_id: int | None = None,
    source_id: int | None = None,
    limit: int = Query(default=DEFAULT_LIMIT, le=MAX_LIMIT),
    offset: int = Query(default=DEFAULT_OFFSET),
    session: Session = Depends(get_session),
):
    query = select(ScrapeJobRecord).order_by(col(ScrapeJobRecord.created_at).desc())
    if feed_id is not None:
        query = query.where(ScrapeJobRecord.feed_id == feed_id)
    if source_id is not None:
        query = query.where(ScrapeJobRecord.source_id == source_id)
    return paginate(session, query, limit, offset)


@router.get("/jobs/{job_id}", response_model=ScrapeJobRecordRead)
def get_job(job_id: int, session: Session = Depends(get_session)):
    return get_or_404(session, ScrapeJobRecord, job_id)


@router.get("/jobs/{job_id}/logs", response_model=list[ScrapeLogRead])
def get_job_logs(job_id: int, session: Session = Depends(get_session)):
    get_or_404(session, ScrapeJobRecord, job_id)
    return session.exec(
        select(ScrapeLog)
        .where(ScrapeLog.job_id == job_id)
        .order_by(col(ScrapeLog.created_at).asc())
    ).all()
