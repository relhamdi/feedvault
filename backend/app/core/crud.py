from fastapi import HTTPException
from sqlmodel import Session, SQLModel, select


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
