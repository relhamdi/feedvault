from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models.collection import (
    Collection,
    CollectionCreate,
    CollectionRead,
    CollectionUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[CollectionRead])
def list_collections(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    session: Session = Depends(get_session),
):
    return session.exec(select(Collection).offset(offset).limit(limit)).all()


@router.get("/{collection_id}", response_model=CollectionRead)
def get_collection(collection_id: int, session: Session = Depends(get_session)):
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.post("/", response_model=CollectionRead, status_code=201)
def create_collection(
    collection_in: CollectionCreate,
    session: Session = Depends(get_session),
):
    collection = Collection.model_validate(collection_in)
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


@router.patch("/{collection_id}", response_model=CollectionRead)
def update_collection(
    collection_id: int,
    collection_in: CollectionUpdate,
    session: Session = Depends(get_session),
):
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    data = collection_in.model_dump(exclude_unset=True)
    collection.sqlmodel_update(data)
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


@router.delete("/{collection_id}", status_code=204)
def delete_collection(collection_id: int, session: Session = Depends(get_session)):
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    session.delete(collection)
    session.commit()
