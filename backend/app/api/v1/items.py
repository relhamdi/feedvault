from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from app.core.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.core.crud import (
    apply_item_filters,
    apply_patch,
    delete_obj,
    get_or_404,
    get_or_404_with_options,
    paginate,
)
from app.core.sorting import ITEM_SORT_COLUMNS, ItemSortField, SortOrder
from app.database import get_session
from app.models.category import Category, CategoryCreate
from app.models.item import Item, ItemCreate, ItemRead, ItemUpdate
from app.models.item_media import ItemMedia, ItemMediaCreate, ItemMediaRead
from app.models.links import ItemCategoryLink
from app.models.pagination import PaginatedResponse


class ItemCreateWithRelations(BaseModel):
    item: ItemCreate
    categories: list[CategoryCreate] = []
    media: list[ItemMediaCreate] = []


router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ItemRead])
def list_items(
    feed_id: int | None = Query(default=None),
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
    query = select(Item).options(
        selectinload(Item.author),  # type: ignore
        selectinload(Item.media),  # type: ignore
        selectinload(Item.categories),  # type: ignore
    )
    if feed_id is not None:
        query = query.where(Item.feed_id == feed_id)
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
    query = query.order_by(order)
    return paginate(session, query, limit, offset)


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, session: Session = Depends(get_session)):
    return get_or_404_with_options(
        session,
        Item,
        item_id,
        selectinload(Item.author),  # type: ignore
        selectinload(Item.media),  # type: ignore
        selectinload(Item.categories),  # type: ignore
    )


@router.post("/", response_model=ItemRead, status_code=201)
def create_item(
    payload: ItemCreateWithRelations,
    session: Session = Depends(get_session),
):
    item = Item.model_validate(payload.item)
    session.add(item)
    session.flush()
    assert item.id is not None

    for category_in in payload.categories:
        # Upsert: Check if category is already created
        existing = session.exec(
            select(Category).where(
                Category.name == category_in.name,
                Category.source_id == category_in.source_id,
            )
        ).first()
        category = existing or Category.model_validate(category_in)
        if not existing:
            session.add(category)
            session.flush()
        session.add(ItemCategoryLink(item_id=item.id, category_id=category.id))

    for media_in in payload.media:
        media = ItemMedia.model_validate(media_in.model_dump() | {"item_id": item.id})
        session.add(media)

    session.commit()
    session.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(
    item_id: int,
    item_in: ItemUpdate,
    session: Session = Depends(get_session),
):
    return apply_patch(session, get_or_404(session, Item, item_id), item_in)


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, session: Session = Depends(get_session)):
    delete_obj(session, get_or_404(session, Item, item_id))


# --- ItemMedia routes ---


@router.get("/{item_id}/media", response_model=list[ItemMediaRead])
def list_item_media(item_id: int, session: Session = Depends(get_session)):
    _ = get_or_404(session, Item, item_id)
    return session.exec(select(ItemMedia).where(ItemMedia.item_id == item_id)).all()


@router.post("/{item_id}/media", response_model=ItemMediaRead, status_code=201)
def add_item_media(
    item_id: int,
    media_in: ItemMediaCreate,
    session: Session = Depends(get_session),
):
    _ = get_or_404(session, Item, item_id)
    media = ItemMedia.model_validate(media_in.model_dump() | {"item_id": item_id})
    session.add(media)
    session.commit()
    session.refresh(media)
    return media


@router.delete("/{item_id}/media/{media_id}", status_code=204)
def delete_item_media(
    item_id: int,
    media_id: int,
    session: Session = Depends(get_session),
):
    media = session.get(ItemMedia, media_id)
    if not media or media.item_id != item_id:
        raise HTTPException(status_code=404, detail="Media not found")
    session.delete(media)
    session.commit()
