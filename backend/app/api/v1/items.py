from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.database import get_session
from app.models.category import Category, CategoryCreate
from app.models.item import Item, ItemCreate, ItemRead, ItemUpdate
from app.models.item_media import ItemMedia, ItemMediaCreate, ItemMediaRead
from app.models.links import ItemCategoryLink

router = APIRouter()


class ItemCreateWithRelations(BaseModel):
    item: ItemCreate
    categories: list[CategoryCreate] = []
    media: list[ItemMediaCreate] = []


@router.get("/", response_model=list[ItemRead])
def list_items(
    feed_id: int | None = Query(default=None),
    is_read: bool | None = Query(default=None),
    is_favorite: bool | None = Query(default=None),
    is_nsfw: bool | None = Query(default=None),
    is_public: bool | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    session: Session = Depends(get_session),
):
    query = select(Item)
    if feed_id is not None:
        query = query.where(Item.feed_id == feed_id)
    if is_read is not None:
        query = query.where(Item.is_read == is_read)
    if is_favorite is not None:
        query = query.where(Item.is_favorite == is_favorite)
    if is_nsfw is not None:
        query = query.where(Item.is_nsfw == is_nsfw)
    if is_public is not None:
        query = query.where(Item.is_public == is_public)
    query = (
        query.order_by(col(Item.source_published_at).desc()).offset(offset).limit(limit)
    )
    return session.exec(query).all()


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=ItemRead, status_code=201)
def create_item(
    payload: ItemCreateWithRelations,
    session: Session = Depends(get_session),
):
    item = Item.model_validate(payload.item)
    session.add(item)
    session.flush()  # Generate ID without commit

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
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    data = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()


# --- ItemMedia routes ---


@router.get("/{item_id}/media", response_model=list[ItemMediaRead])
def list_item_media(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return session.exec(select(ItemMedia).where(ItemMedia.item_id == item_id)).all()


@router.post("/{item_id}/media", response_model=ItemMediaRead, status_code=201)
def add_item_media(
    item_id: int,
    media_in: ItemMediaCreate,
    session: Session = Depends(get_session),
):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
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
