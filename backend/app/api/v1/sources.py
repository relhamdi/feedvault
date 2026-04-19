from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.crypto import encrypt_credentials
from app.core.sources.registry import _REGISTRY, get_registration, registered_slugs
from app.database import get_session
from app.models.source import Source, SourceCreate, SourceRead, SourceUpdate

router = APIRouter()


class BootstrapAllResult(BaseModel):
    created: list[SourceRead]
    existing: list[SourceRead]


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


@router.put("/{source_id}/credentials", response_model=SourceRead)
def update_credentials(
    source_id: int,
    credentials: dict,
    session: Session = Depends(get_session),
):
    """Encrypt and store credentials for a source."""
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.credentials = encrypt_credentials(credentials)
    source.updated_at = datetime.now(UTC)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


# --- Bootstrap routes ---


def _bootstrap_one(slug: str, session: Session) -> tuple[Source, bool]:
    """Create a source from its registered default_source metadata."""
    reg = get_registration(slug)
    if reg is None:
        raise HTTPException(
            status_code=404,
            detail=f"No scraper registered for slug '{slug}'. "
            f"Available: {registered_slugs() or 'none'}",
        )
    if not reg.default_source:
        raise HTTPException(
            status_code=400,
            detail=f"Scraper '{slug}' has no default_source metadata defined.",
        )

    existing = session.exec(select(Source).where(Source.slug == slug)).first()
    if existing:
        return existing, False

    source = Source.model_validate({**reg.default_source, "slug": slug})
    session.add(source)
    session.commit()
    session.refresh(source)
    return source, True


@router.post("/bootstrap/{slug}", response_model=SourceRead)
def bootstrap_source(
    slug: str,
    response: Response,
    session: Session = Depends(get_session),
):
    """Initialize a single source from its scraper's default metadata.

    Returns 201 if created, 200 if the source already existed.
    """
    source, created = _bootstrap_one(slug, session)
    response.status_code = 201 if created else 200
    return source


@router.post("/bootstrap", response_model=BootstrapAllResult)
def bootstrap_all_sources(session: Session = Depends(get_session)):
    """Initialize all sources that have default_source metadata defined.

    Skips sources already present in the database.
    Returns the list of all bootstrapped sources (created or existing).
    """

    created, existing = [], []
    for slug, reg in _REGISTRY.items():
        if not reg.default_source:
            continue
        source, was_created = _bootstrap_one(slug, session)
        (created if was_created else existing).append(source)
    return BootstrapAllResult(created=created, existing=existing)


@router.get("/bootstrap/{slug}/credentials-schema")
def get_credentials_schema(slug: str) -> dict:
    """Return the expected credentials schema for a registered scraper."""
    reg = get_registration(slug)
    if reg is None:
        raise HTTPException(
            status_code=404,
            detail=f"No scraper registered for slug '{slug}'.",
        )
    return reg.credentials_schema
