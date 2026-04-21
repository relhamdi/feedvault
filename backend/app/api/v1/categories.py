from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.core.crud import delete_obj, get_or_404, paginate
from app.database import get_session
from app.models.category import Category, CategoryCreate, CategoryRead
from app.models.pagination import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[CategoryRead])
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
    return paginate(session, query, limit, offset)


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, session: Session = Depends(get_session)):
    return get_or_404(session, Category, category_id)


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
    delete_obj(session, get_or_404(session, Category, category_id))
