from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models.source import Source, SourceCreate, SourceRead, SourceUpdate

router = APIRouter()


@router.get("/", response_model=list[SourceRead])
def list_sources(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    session: Session = Depends(get_session),
):
    return session.exec(select(Source).offset(offset).limit(limit)).all()


@router.get("/{source_id}", response_model=SourceRead)
def get_source(source_id: int, session: Session = Depends(get_session)):
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.post("/", response_model=SourceRead, status_code=201)
def create_source(source_in: SourceCreate, session: Session = Depends(get_session)):
    source = Source.model_validate(source_in)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.patch("/{source_id}", response_model=SourceRead)
def update_source(
    source_id: int,
    source_in: SourceUpdate,
    session: Session = Depends(get_session),
):
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    data = source_in.model_dump(exclude_unset=True)
    source.sqlmodel_update(data)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, session: Session = Depends(get_session)):
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    session.delete(source)
    session.commit()
