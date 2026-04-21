from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, SQLModel, select

from app.models.pagination import PaginatedResponse


def paginate(session: Session, query, limit: int, offset: int) -> PaginatedResponse:
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
    items = session.exec(query.offset(offset).limit(limit)).all()
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


def get_or_404(session: Session, model: type, id: int):
    obj = session.get(model, id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


def get_or_404_with_options(session: Session, model: type, id: int, *options):
    query = select(model).where(model.id == id)
    for opt in options:
        query = query.options(opt)
    obj = session.exec(query).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


def apply_patch(session: Session, obj: SQLModel, patch: SQLModel) -> SQLModel:
    data = patch.model_dump(exclude_unset=True)
    obj.sqlmodel_update(data)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def delete_obj(session: Session, obj: SQLModel) -> None:
    session.delete(obj)
    session.commit()
