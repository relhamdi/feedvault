from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.core.crud import delete_obj, get_or_404, paginate
from app.database import get_session
from app.models.author import Author, AuthorCreate, AuthorRead
from app.models.pagination import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[AuthorRead])
def list_authors(
    source_id: int | None = Query(default=None),
    limit: int = Query(default=DEFAULT_LIMIT, le=MAX_LIMIT),
    offset: int = Query(default=DEFAULT_OFFSET),
    session: Session = Depends(get_session),
):
    query = select(Author)
    if source_id is not None:
        query = query.where(Author.source_id == source_id)
    return paginate(session, query, limit, offset)


@router.get("/{author_id}", response_model=AuthorRead)
def get_author(author_id: int, session: Session = Depends(get_session)):
    return get_or_404(session, Author, author_id)


@router.post("/", response_model=AuthorRead, status_code=201)
def create_author(author_in: AuthorCreate, session: Session = Depends(get_session)):
    author = Author.model_validate(author_in)
    session.add(author)
    session.commit()
    session.refresh(author)
    return author


@router.delete("/{author_id}", status_code=204)
def delete_author(author_id: int, session: Session = Depends(get_session)):
    delete_obj(session, get_or_404(session, Author, author_id))
