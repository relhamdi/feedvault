from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, SQLModel, col, or_, select

from app.core.tags import normalize_tags
from app.models.item import Item
from app.models.pagination import PaginatedResponse


def paginate(session: Session, query, limit: int, offset: int) -> PaginatedResponse:
    """Return paginated results and total count for a query."""
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
    items = session.exec(query.offset(offset).limit(limit)).all()
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


def get_or_404(session: Session, model: type, id: int):
    """Get object by ID or raise HTTP 404 if not found."""
    obj = session.get(model, id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


def get_or_404_with_options(session: Session, model: type, id: int, *options):
    """Get object by ID with query options or raise HTTP 404 if not found."""
    query = select(model).where(model.id == id)
    for opt in options:
        query = query.options(opt)
    obj = session.exec(query).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


def apply_patch(session: Session, obj: SQLModel, patch: SQLModel) -> SQLModel:
    """Apply updated fields to an object in the database."""
    data = patch.model_dump(exclude_unset=True)
    obj.sqlmodel_update(data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def delete_obj(session: Session, obj: SQLModel) -> None:
    """Delete given object from the database."""
    session.delete(obj)
    session.commit()


def apply_item_filters(
    query,
    is_read: bool | None = None,
    is_favorite: bool | None = None,
    is_nsfw: bool | None = None,
    is_public: bool | None = None,
    search: str | None = None,
    tags: list[str] | None = None,
):
    if is_read is not None:
        query = query.where(Item.is_read == is_read)
    if is_favorite is not None:
        query = query.where(Item.is_favorite == is_favorite)
    if is_nsfw is not None:
        query = query.where(Item.is_nsfw == is_nsfw)
    if is_public is not None:
        query = query.where(Item.is_public == is_public)
    if search:
        query = query.where(
            or_(
                col(Item.title).ilike(f"%{search}%"),
                col(Item.summary).ilike(f"%{search}%"),
            )
        )
    if tags:
        for tag in normalize_tags(tags):
            query = query.where(col(Item.tags).contains(tag))
    return query
