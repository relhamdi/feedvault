from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.database import get_session
from app.models.category import Category, CategoryCreate, CategoryRead

router = APIRouter()


@router.get("/", response_model=list[CategoryRead])
def list_categories(
    source_id: int | None = Query(default=None),
    parent_id: int | None = Query(default=None),
    limit: int = Query(default=DEFAULT_LIMIT, le=MAX_LIMIT),
    offset: int = Query(default=DEFAULT_OFFSET),
    session: Session = Depends(get_session),
):
    query = select(Category)
    if source_id is not None:
        query = query.where(Category.source_id == source_id)
    if parent_id is not None:
        query = query.where(Category.parent_id == parent_id)
    query = query.offset(offset).limit(limit)
    return session.exec(query).all()


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/", response_model=CategoryRead, status_code=201)
def create_category(
    category_in: CategoryCreate, session: Session = Depends(get_session)
):
    category = Category.model_validate(category_in)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(category)
    session.commit()
