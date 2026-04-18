from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, and_, col, or_, select

from app.core.tags import normalize_tags
from app.database import get_session
from app.models.collection import (
    Collection,
    CollectionCreate,
    CollectionRead,
    CollectionUpdate,
    FilterOperator,
)
from app.models.feed import Feed
from app.models.item import Item, ItemRead

router = APIRouter()


@router.get("/", response_model=list[CollectionRead])
def list_collections(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    session: Session = Depends(get_session),
):
    return session.exec(select(Collection).offset(offset).limit(limit)).all()


@router.get("/{collection_id}", response_model=CollectionRead)
def get_collection(collection_id: int, session: Session = Depends(get_session)):
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.post("/", response_model=CollectionRead, status_code=201)
def create_collection(
    collection_in: CollectionCreate,
    session: Session = Depends(get_session),
):
    collection = Collection.model_validate(collection_in)
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


@router.patch("/{collection_id}", response_model=CollectionRead)
def update_collection(
    collection_id: int,
    collection_in: CollectionUpdate,
    session: Session = Depends(get_session),
):
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    data = collection_in.model_dump(exclude_unset=True)
    collection.sqlmodel_update(data)
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


@router.delete("/{collection_id}", status_code=204)
def delete_collection(collection_id: int, session: Session = Depends(get_session)):
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    session.delete(collection)
    session.commit()


@router.get("/{collection_id}/items", response_model=list[ItemRead])
def get_collection_items(
    collection_id: int,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    session: Session = Depends(get_session),
):
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    filters = _build_filters(collection)
    if not filters:
        return []

    if collection.filter_operator == FilterOperator.AND:
        query = select(Item).where(and_(*filters))
    else:
        query = select(Item).where(or_(*filters))

    query = (
        query.distinct()
        .order_by(col(Item.source_updated_at).desc())
        .offset(offset)
        .limit(limit)
    )

    return session.exec(query).all()


def _build_filters(collection: Collection) -> list:
    """
    Build SQLAlchemy filter expressions from collection criteria.
    Each criterion (sources, feeds, tags) produces one filter clause.
    """
    filters = []

    if collection.filter_source_ids:
        # Match items whose feed belongs to one of the source ids
        feeds_subquery = select(Feed.id).where(
            col(Feed.source_id).in_(collection.filter_source_ids)
        )
        filters.append(col(Item.feed_id).in_(feeds_subquery))

    if collection.filter_feed_ids:
        filters.append(col(Item.feed_id).in_(collection.filter_feed_ids))

    if collection.filter_tags:
        normalized = normalize_tags(collection.filter_tags)
        tag_filters = [col(Item.tags).contains(tag) for tag in normalized]
        # Tags within a single criterion are always OR (item must have at least one of the requested tags)
        filters.append(or_(*tag_filters))

    return filters
