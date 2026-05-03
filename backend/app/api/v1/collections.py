from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import Session, and_, col, or_, select

from app.core.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.core.crud import (
    apply_item_filters,
    apply_patch,
    delete_obj,
    get_or_404,
    paginate,
)
from app.core.sorting import ITEM_SORT_COLUMNS, ItemSortField, SortOrder
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
from app.models.pagination import PaginatedResponse
from app.models.stats import CollectionStats

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[CollectionRead])
def list_collections(
    limit: int = Query(default=DEFAULT_LIMIT, le=MAX_LIMIT),
    offset: int = Query(default=DEFAULT_OFFSET),
    session: Session = Depends(get_session),
):
    query = select(Collection)
    return paginate(session, query, limit, offset)


@router.get("/{collection_id}", response_model=CollectionRead)
def get_collection(collection_id: int, session: Session = Depends(get_session)):
    return get_or_404(session, Collection, collection_id)


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
    return apply_patch(
        session,
        get_or_404(session, Collection, collection_id),
        collection_in,
    )


@router.delete("/{collection_id}", status_code=204)
def delete_collection(collection_id: int, session: Session = Depends(get_session)):
    delete_obj(session, get_or_404(session, Collection, collection_id))


@router.get("/{collection_id}/items", response_model=PaginatedResponse[ItemRead])
def get_collection_items(
    collection_id: int,
    is_read: bool | None = Query(default=None),
    is_favorite: bool | None = Query(default=None),
    is_nsfw: bool | None = Query(default=None),
    is_public: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    tags: list[str] | None = Query(default=None),
    sort_by: ItemSortField = Query(default=ItemSortField.SOURCE_UPDATED_AT),
    sort_order: SortOrder = Query(default=SortOrder.DESC),
    limit: int = Query(default=DEFAULT_LIMIT, le=MAX_LIMIT),
    offset: int = Query(default=DEFAULT_OFFSET),
    session: Session = Depends(get_session),
):
    collection = get_or_404(session, Collection, collection_id)
    filters = _build_filters(collection)
    if not filters:
        return PaginatedResponse(items=[], total=0, limit=limit, offset=offset)

    if collection.filter_operator == FilterOperator.AND:
        query = select(Item).where(and_(*filters))
    else:
        query = select(Item).where(or_(*filters))

    query = apply_item_filters(
        query,
        is_read,
        is_favorite,
        is_nsfw,
        is_public,
        search,
        tags,
    )

    order = (
        col(ITEM_SORT_COLUMNS[sort_by]).desc()
        if sort_order == SortOrder.DESC
        else col(ITEM_SORT_COLUMNS[sort_by]).asc()
    )
    query = query.distinct().order_by(order)
    return paginate(session, query, limit, offset)


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


@router.get("/{collection_id}/stats", response_model=CollectionStats)
def get_collection_stats(
    collection_id: int,
    session: Session = Depends(get_session),
):
    collection = get_or_404(session, Collection, collection_id)
    filters = _build_filters(collection)
    if not filters:
        return CollectionStats(total=0, unread=0)

    if collection.filter_operator == FilterOperator.AND:
        base = select(Item).where(and_(*filters)).distinct()
    else:
        base = select(Item).where(or_(*filters)).distinct()

    total = session.exec(select(func.count()).select_from(base.subquery())).one()
    unread = session.exec(
        select(func.count()).select_from(base.where(~Item.is_read).subquery())  # type: ignore
    ).one()

    return CollectionStats(
        total=total or 0,
        unread=unread or 0,
    )
