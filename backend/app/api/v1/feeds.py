from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models.feed import Feed, FeedCreate, FeedRead, FeedUpdate

router = APIRouter()


@router.get("/", response_model=list[FeedRead])
def list_feeds(
    source_id: int | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    session: Session = Depends(get_session),
):
    query = select(Feed)
    if source_id is not None:
        query = query.where(Feed.source_id == source_id)
    query = query.offset(offset).limit(limit)
    return session.exec(query).all()


@router.get("/{feed_id}", response_model=FeedRead)
def get_feed(feed_id: int, session: Session = Depends(get_session)):
    feed = session.get(Feed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return feed


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
    feed = session.get(Feed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    data = feed_in.model_dump(exclude_unset=True)
    feed.sqlmodel_update(data)
    session.add(feed)
    session.commit()
    session.refresh(feed)
    return feed


@router.delete("/{feed_id}", status_code=204)
def delete_feed(feed_id: int, session: Session = Depends(get_session)):
    feed = session.get(Feed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    session.delete(feed)
    session.commit()
