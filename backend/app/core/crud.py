from fastapi import HTTPException
from sqlmodel import Session, SQLModel


def get_or_404(session: Session, model: type, id: int):
    obj = session.get(model, id)
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
