from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlmodel import Session, select

from app.core.constants import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_LIMIT
from app.core.crud import apply_patch, delete_obj, get_or_404, paginate
from app.core.crypto import encrypt_credentials
from app.core.sources.registry import _REGISTRY, get_registration, registered_slugs
from app.database import get_session
from app.models.feed import Feed
from app.models.item import Item
from app.models.pagination import PaginatedResponse
from app.models.source import Source, SourceCreate, SourceRead, SourceUpdate
from app.models.stats import SourceStats

router = APIRouter()


class BootstrapAllResult(BaseModel):
    created: list[SourceRead]
    existing: list[SourceRead]


@router.get("/", response_model=PaginatedResponse[SourceRead])
def list_sources(
    limit: int = Query(default=DEFAULT_LIMIT, le=MAX_LIMIT),
    offset: int = Query(default=DEFAULT_OFFSET),
    session: Session = Depends(get_session),
):
    query = select(Source)
    return paginate(session, query, limit, offset)


@router.get("/{source_id}", response_model=SourceRead)
def get_source(source_id: int, session: Session = Depends(get_session)):
    return get_or_404(session, Source, source_id)


@router.post("/", response_model=SourceRead, status_code=201)
def create_source(source_in: SourceCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(Source).where(Source.slug == source_in.slug)).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Source with slug '{source_in.slug}' already exists.",
        )
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
    return apply_patch(session, get_or_404(session, Source, source_id), source_in)


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, session: Session = Depends(get_session)):
    delete_obj(session, get_or_404(session, Source, source_id))


@router.get("/{source_id}/stats", response_model=SourceStats)
def get_source_stats(source_id: int, session: Session = Depends(get_session)):
    _ = get_or_404(session, Source, source_id)

    item_row = session.exec(
        select(
            func.count(Item.id).label("total"),  # type: ignore
            func.sum(case((~Item.is_read, 1), else_=0)).label("unread"),  # type: ignore
            func.sum(case((Item.is_favorite, 1), else_=0)).label("favorite"),  # type: ignore
            func.sum(case((Item.is_nsfw, 1), else_=0)).label("nsfw"),  # type: ignore
            func.sum(case((~Item.is_public, 1), else_=0)).label("not_public"),  # type: ignore
        )  # type: ignore
        .join(Feed, Item.feed_id == Feed.id)
        .where(Feed.source_id == source_id)
    ).one()

    feeds_count, active_feeds_count = session.exec(
        select(
            func.count(Feed.id).label("feeds_count"),  # type: ignore
            func.sum(case((Feed.is_active, 1), else_=0)).label("active_feeds_count"),  # type: ignore
        ).where(Feed.source_id == source_id)
    ).one()

    return SourceStats(
        total=item_row.total or 0,
        unread=item_row.unread or 0,
        favorite=item_row.favorite or 0,
        nsfw=item_row.nsfw or 0,
        not_public=item_row.not_public or 0,
        feeds_count=feeds_count or 0,
        active_feeds_count=active_feeds_count or 0,
    )


@router.put("/{source_id}/credentials", response_model=SourceRead)
def update_credentials(
    source_id: int,
    credentials: dict,
    session: Session = Depends(get_session),
):
    """Encrypt and store credentials for a source."""
    source = get_or_404(session, Source, source_id)
    source.credentials = encrypt_credentials(credentials)
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


@router.get("/bootstrap/{slug}/params-schema")
def get_params_schema_route(slug: str) -> dict:
    """Return the expected params keys for a registered scraper."""
    reg = get_registration(slug)
    if reg is None:
        raise HTTPException(
            status_code=404,
            detail=f"No scraper registered for slug '{slug}'.",
        )
    return reg.params_schema


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
