from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlmodel import Session, select

from app.core.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.core.crud import apply_patch, delete_obj, get_or_404, paginate
from app.database import get_session
from app.models.feed import Feed, FeedCreate, FeedRead, FeedUpdate
from app.models.item import Item
from app.models.pagination import PaginatedResponse
from app.models.stats import FeedStats

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[FeedRead])
def list_feeds(
    source_id: int | None = Query(default=None),
    limit: int = Query(default=DEFAULT_LIMIT, le=MAX_LIMIT),
    offset: int = Query(default=DEFAULT_OFFSET),
    session: Session = Depends(get_session),
):
    query = select(Feed)
    if source_id is not None:
        query = query.where(Feed.source_id == source_id)
    return paginate(session, query, limit, offset)


@router.get("/{feed_id}", response_model=FeedRead)
def get_feed(feed_id: int, session: Session = Depends(get_session)):
    return get_or_404(session, Feed, feed_id)


@router.post("/", response_model=FeedRead, status_code=201)
def create_feed(feed_in: FeedCreate, session: Session = Depends(get_session)):
    feed = Feed.model_validate(feed_in)
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return feed


@router.patch("/{feed_id}", response_model=FeedRead)
def update_feed(
    feed_id: int,
    feed_in: FeedUpdate,
    session: Session = Depends(get_session),
):
    return apply_patch(session, get_or_404(session, Feed, feed_id), feed_in)


@router.delete("/{feed_id}", status_code=204)
def delete_feed(feed_id: int, session: Session = Depends(get_session)):
    delete_obj(session, get_or_404(session, Feed, feed_id))


@router.get("/{feed_id}/stats", response_model=FeedStats)
def get_feed_stats(feed_id: int, session: Session = Depends(get_session)):
    _ = get_or_404(session, Feed, feed_id)

    row = session.exec(
        select(
            func.count(Item.id).label("total"),  # type: ignore
            func.sum(case((~Item.is_read, 1), else_=0)).label("unread"),  # type: ignore
            func.sum(case((Item.is_favorite, 1), else_=0)).label("favorite"),  # type: ignore
            func.sum(case((Item.is_nsfw, 1), else_=0)).label("nsfw"),  # type: ignore
            func.sum(case((~Item.is_public, 1), else_=0)).label("not_public"),  # type: ignore
        ).where(Item.feed_id == feed_id)  # type: ignore
    ).one()
    return FeedStats(
        total=row.total or 0,
        unread=row.unread or 0,
        favorite=row.favorite or 0,
        nsfw=row.nsfw or 0,
        not_public=row.not_public or 0,
    )
