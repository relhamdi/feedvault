import json
import shutil
import traceback
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from app.config import settings
from app.core.data_export import (
    serialize_collection,
    serialize_source,
)
from app.core.data_import import (
    check_version,
    import_collection,
    import_feed,
    import_item,
    import_source,
)
from app.database import get_session
from app.models.category import Category
from app.models.collection import Collection
from app.models.export import (
    CURRENT_EXPORT_SCHEMA_VERSION,
    ConflictStrategy,
    ExportOptions,
    ExportSelection,
    ImportParams,
    ImportReport,
)
from app.models.feed import Feed
from app.models.item import Item
from app.models.source import Source

router = APIRouter()


@router.post("/export")
def export_data(
    selection: ExportSelection,
    options: ExportOptions,
    session: Session = Depends(get_session),
):
    """
    Export selected data as a downloadable JSON file.

    Selection logic:
    - feed_ids: export all items belonging to these feeds
    - Empty selection (all lists empty): full export
    - collection_ids: included as collection metadata (references resolved to slugs/urls)
    """
    full_export = not selection.feed_ids

    # Load feeds (and their parent sources)
    if full_export:
        feeds_query = select(Feed)
    else:
        feeds_query = select(Feed).where(col(Feed.id).in_(selection.feed_ids))
    feeds = session.exec(feeds_query).all()

    # Group feeds by source_id
    source_ids = {f.source_id for f in feeds}
    sources = session.exec(select(Source).where(col(Source.id).in_(source_ids))).all()
    source_map: dict[int, Source] = {s.id: s for s in sources if s.id}
    feeds_by_source: dict[int, list[Feed]] = {}
    for feed in feeds:
        feeds_by_source.setdefault(feed.source_id, []).append(feed)

    # Build category index for parent_name resolution
    cat_index: dict[int, Category] = {
        c.id: c for c in session.exec(select(Category)).all() if c.id is not None
    }

    # Build lookup maps for collection serialization
    source_id_to_slug: dict[int, str] = {s.id: s.slug for s in sources if s.id}
    feed_id_to_ref: dict[int, dict[str, str]] = {
        f.id: {"source_slug": source_map[f.source_id].slug, "feed_url": f.url}
        for f in feeds
        if f.id and f.source_id in source_map
    }

    # Serialize sources + feeds
    exported_sources = []

    for source in sources:
        assert source.id is not None
        source_feeds = feeds_by_source.get(source.id, [])
        feeds_items: list[tuple[Feed, list[Item]]] = []

        for feed in source_feeds:
            assert feed.id is not None
            items_query = (
                select(Item)
                .where(Item.feed_id == feed.id)
                .options(
                    selectinload(Item.author),  # type: ignore
                    selectinload(Item.categories),  # type: ignore
                    selectinload(Item.media),  # type: ignore
                )
            )
            items = session.exec(items_query).all()
            feeds_items.append((feed, list(items)))

        exported_sources.append(
            serialize_source(source, feeds_items, cat_index, options)
        )

    # Collections
    exported_collections = []
    if options.include_collections:
        if selection.collection_ids:
            collections = session.exec(
                select(Collection).where(
                    col(Collection.id).in_(selection.collection_ids)
                )
            ).all()
        else:
            collections = session.exec(select(Collection)).all()

        exported_collections = [
            serialize_collection(c, source_id_to_slug, feed_id_to_ref)
            for c in collections
        ]

    # Build final document
    doc = {
        "export_schema_version": CURRENT_EXPORT_SCHEMA_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "options": options.model_dump(),
        "sources": exported_sources,
        "collections": exported_collections,
    }

    filename = f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}-feedvault_export.json"
    content = json.dumps(doc, indent=2, default=str)

    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import", response_model=ImportReport)
async def import_data(
    file: UploadFile = File(...),
    conflict_strategy: ConflictStrategy = Query(default=ConflictStrategy.UPSERT),
    redownload_missing_images: bool = Query(default=False),
    session: Session = Depends(get_session),
):
    """Import data from a FeedVault export JSON file."""
    params = ImportParams(
        conflict_strategy=conflict_strategy,
        redownload_missing_images=redownload_missing_images,
    )
    report = ImportReport()

    # Parse file
    try:
        content = await file.read()
        raw = json.loads(content)
    except Exception as e:
        report.errors.append(f"Failed to parse JSON: {e}")
        return report

    # Version check
    try:
        check_version(raw.get("export_schema_version", ""))
    except ValueError as e:
        report.errors.append(str(e))
        return report

    # Import in one transaction
    try:
        source_slug_to_id: dict[str, int] = {}
        feed_ref_to_id: dict[tuple[str, str], int] = {}

        for raw_source in raw.get("sources", []):
            source = import_source(session, raw_source, params, report)
            if not source:
                continue
            assert source.id is not None
            source_slug_to_id[source.slug] = source.id

            # Per-source category cache to avoid redundant queries
            cat_cache: dict[str, Category] = {}

            for raw_feed in raw_source.get("feeds", []):
                feed = import_feed(session, raw_feed, source, params, report)
                if not feed:
                    continue
                assert feed.id is not None
                feed_ref_to_id[(source.slug, feed.url)] = feed.id

                for raw_item in raw_feed.get("items", []):
                    import_item(
                        session,
                        raw_item,
                        feed,
                        source,
                        params,
                        report,
                        cat_cache,
                    )

        for raw_col in raw.get("collections", []):
            import_collection(
                session,
                raw_col,
                source_slug_to_id,
                feed_ref_to_id,
                params,
                report,
            )

        session.commit()
        report.success = True

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        report.errors.append(f"Import failed: {e}")

    return report


@router.delete("/reset", status_code=204)
def reset_database(session: Session = Depends(get_session)):
    session.exec(delete(Collection))
    # Source will cascade delete the rest
    session.exec(delete(Source))
    session.commit()

    # Clean up in the media folder
    media_dir = Path(settings.media_dir)
    if media_dir.exists():
        shutil.rmtree(media_dir)
        media_dir.mkdir()
