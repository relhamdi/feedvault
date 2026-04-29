from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from app.config import settings
from app.core.crypto import encrypt_credentials
from app.core.image import download_and_compress
from app.models.author import Author
from app.models.category import Category
from app.models.collection import Collection
from app.models.export import SUPPORTED_IMPORT_VERSIONS, ConflictStrategy, ImportParams, ImportReport
from app.models.feed import Feed
from app.models.item import Item
from app.models.item_media import ItemMedia
from app.models.source import Source

DATETIME_FIELDS_SOURCE = {"created_at", "updated_at", "last_scraped_at"}
DATETIME_FIELDS_FEED = {"created_at", "updated_at", "last_scraped_at"}
DATETIME_FIELDS_ITEM = {
    "created_at",
    "updated_at",
    "scraped_at",
    "last_scraped_at",
    "last_seen_at",
    "source_published_at",
    "source_updated_at",
}
DATETIME_FIELDS_AUTHOR = {"created_at", "updated_at"}
DATETIME_FIELDS_MEDIA = {"created_at"}


# --- Helpers ---


def _parse_datetimes(data: dict, fields: set[str]) -> dict:
    """Convert ISO string datetimes to datetime objects for SQLModel compatibility.

    Args:
        data (dict): Data dict.
        fields (set[str]): Datetime field names.

    Returns:
        dict: Dict with converted datetime objects.
    """
    result = dict(data)
    for field in fields:
        val = result.get(field)
        if isinstance(val, str):
            try:
                result[field] = datetime.fromisoformat(val)
            except ValueError:
                pass
    return result


def check_version(version: str) -> None:
    if version not in SUPPORTED_IMPORT_VERSIONS:
        raise ValueError(
            f"Unsupported export schema version '{version}'. "
            f"Supported: {SUPPORTED_IMPORT_VERSIONS}"
        )


# --- Source import ---


def _import_credentials(source: Source, raw: dict, report: ImportReport) -> None:
    creds = raw.get("credentials")
    if creds and isinstance(creds, dict):
        try:
            source.credentials = encrypt_credentials(creds)
        except Exception as e:
            report.warnings.append(
                f"Source '{source.slug}': failed to encrypt credentials — {e}"
            )


def import_source(
    session: Session,
    raw: dict,
    params: ImportParams,
    report: ImportReport,
) -> Source | None:
    slug = raw.get("slug")
    if not slug:
        report.errors.append("Source missing 'slug', skipped.")
        return None

    existing = session.exec(select(Source).where(Source.slug == slug)).first()

    if existing:
        if params.conflict_strategy == ConflictStrategy.SKIP:
            report.sources_skipped += 1
            return existing  # Still return so children can be imported

        # Upsert: update fields but keep credentials unless provided
        cleaned = _parse_datetimes(
            {k: v for k, v in raw.items() if k not in ("credentials", "feeds")},
            DATETIME_FIELDS_SOURCE,
        )
        for key, value in cleaned.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        _import_credentials(existing, raw, report)
        session.add(existing)
        session.flush()
        report.sources_skipped += 1  # If existing, not counted as created
        return existing

    # Create new
    source_data = _parse_datetimes(
        {k: v for k, v in raw.items() if k not in ("credentials", "feeds")},
        DATETIME_FIELDS_SOURCE,
    )
    source = Source(**source_data)
    _import_credentials(source, raw, report)
    session.add(source)
    session.flush()
    report.sources_created += 1
    return source


# --- Feed import ---


def import_feed(
    session: Session,
    raw: dict,
    source: Source,
    params: ImportParams,
    report: ImportReport,
) -> Feed | None:
    url = raw.get("url")
    if not url:
        report.errors.append(f"Feed in source '{source.slug}' missing 'url', skipped.")
        return None

    assert source.id is not None
    existing = session.exec(
        select(Feed).where(Feed.source_id == source.id, Feed.url == url)
    ).first()

    if existing:
        if params.conflict_strategy == ConflictStrategy.SKIP:
            report.feeds_skipped += 1
            return existing  # Still return so children can be imported

        cleaned = _parse_datetimes(
            {k: v for k, v in raw.items() if k != "items"},
            DATETIME_FIELDS_FEED,
        )
        for key, value in cleaned.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        existing.source_id = source.id
        session.add(existing)
        session.flush()
        report.feeds_skipped += 1  # If existing, not counted as created
        return existing

    # Create new
    feed_data = _parse_datetimes(
        {k: v for k, v in raw.items() if k != "items"},
        DATETIME_FIELDS_FEED,
    )
    feed_data["source_id"] = source.id
    feed = Feed(**feed_data)
    session.add(feed)
    session.flush()
    report.feeds_created += 1
    return feed


# --- Author import ---


def _get_or_create_author(
    session: Session,
    raw_author: dict,
    source: Source,
) -> Author:
    assert source.id is not None
    external_id = raw_author.get("external_id", "")
    existing = session.exec(
        select(Author).where(
            Author.source_id == source.id,
            Author.external_id == external_id,
        )
    ).first()
    if existing:
        return existing

    author_data = _parse_datetimes(dict(raw_author), DATETIME_FIELDS_AUTHOR)
    author_data["source_id"] = source.id
    author = Author(**author_data)
    session.add(author)
    session.flush()
    return author


# --- Category import ---


def _get_or_create_category(
    session: Session,
    name: str,
    parent_name: str | None,
    source: Source,
    cat_cache: dict[str, Category],
) -> Category:
    """
    cat_cache keys are category names (within this source context).
    Parent is resolved from the same cache, caller must ensure roots are created before children
    (two-pass at call site).
    """
    assert source.id is not None
    cache_key = name

    if cache_key in cat_cache:
        return cat_cache[cache_key]

    existing = session.exec(
        select(Category).where(
            Category.source_id == source.id,
            Category.name == name,
        )
    ).first()
    if existing:
        cat_cache[cache_key] = existing
        return existing

    parent_id: int | None = None
    if parent_name:
        parent = cat_cache.get(parent_name)
        if parent:
            parent_id = parent.id

    cat = Category(name=name, source_id=source.id, parent_id=parent_id)
    session.add(cat)
    session.flush()
    cat_cache[cache_key] = cat
    return cat


# --- Item (+ ItemMedia) import ---


def _create_media(session: Session, raw_media: list[dict], item: Item) -> None:
    assert item.id is not None
    for m in raw_media:
        media_data = _parse_datetimes(dict(m), DATETIME_FIELDS_MEDIA)
        media_data["item_id"] = item.id
        media = ItemMedia(**media_data)
        session.add(media)


def _handle_image(item: Item, params: ImportParams, report: ImportReport) -> None:
    """
    Re-download thumbnail from thumbnail_url
    if the local file is missing and redownload_missing_images is enabled.
    """
    if not params.redownload_missing_images:
        return
    if not item.thumbnail_url or not item.thumbnail_path:
        return

    dest = Path(settings.media_dir) / item.thumbnail_path
    if dest.exists():
        return  # Already present, nothing to do

    try:
        download_and_compress(item.thumbnail_url, dest)
        report.images_downloaded += 1
    except Exception as e:
        report.images_failed += 1
        report.warnings.append(
            f"Item '{item.external_id}': failed to download thumbnail — {e}"
        )


def import_item(
    session: Session,
    raw: dict,
    feed: Feed,
    source: Source,
    params: ImportParams,
    report: ImportReport,
    cat_cache: dict[str, Category],
) -> None:
    external_id = raw.get("external_id")
    if not external_id:
        report.errors.append(
            f"Item in feed '{feed.url}' missing 'external_id', skipped."
        )
        return

    assert feed.id is not None
    existing = session.exec(
        select(Item).where(
            Item.feed_id == feed.id,
            Item.external_id == external_id,
        )
    ).first()

    # Resolve author
    author_id: int | None = None
    raw_author = raw.get("author")
    if raw_author:
        author = _get_or_create_author(session, raw_author, source)
        author_id = author.id

    # Resolve categories (two-pass: roots first, then children)
    raw_categories: list[dict] = raw.get("categories", [])
    roots = [c for c in raw_categories if not c.get("parent_name")]
    children = [c for c in raw_categories if c.get("parent_name")]
    resolved_cats: list[Category] = []
    for cat_raw in roots + children:
        cat = _get_or_create_category(
            session,
            name=cat_raw["name"],
            parent_name=cat_raw.get("parent_name"),
            source=source,
            cat_cache=cat_cache,
        )
        resolved_cats.append(cat)

    if existing:
        if params.conflict_strategy == ConflictStrategy.SKIP:
            report.items_skipped += 1
            return

        # Update scalar fields
        skip_keys = {"author", "categories", "media", "feed_id", "author_id"}
        cleaned = _parse_datetimes(
            {k: v for k, v in raw.items() if k not in skip_keys},
            DATETIME_FIELDS_ITEM,
        )
        for key, value in cleaned.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        existing.author_id = author_id

        # Sync categories
        existing.categories = resolved_cats

        # Sync media (replace all)
        for m in existing.media:
            session.delete(m)
        session.flush()
        session.refresh(existing)  # Clean up deleted instances
        _create_media(session, raw.get("media", []), existing)

        # Handle image
        _handle_image(existing, params, report)

        session.add(existing)
        session.flush()
        report.items_updated += 1
        return

    # Create new
    item_data = _parse_datetimes(
        {k: v for k, v in raw.items() if k not in ("author", "categories", "media")},
        DATETIME_FIELDS_ITEM,
    )
    item_data["feed_id"] = feed.id
    item_data["author_id"] = author_id
    item = Item(**item_data)
    session.add(item)
    session.flush()

    # Link categories
    item.categories = resolved_cats

    # Create media
    _create_media(session, raw.get("media", []), item)

    # Handle image
    _handle_image(item, params, report)

    session.flush()
    report.items_created += 1


# --- Collection import ---


def import_collection(
    session: Session,
    raw: dict,
    source_slug_to_id: dict[str, int],
    feed_ref_to_id: dict[tuple[str, str], int],
    params: ImportParams,
    report: ImportReport,
) -> None:
    name = raw.get("name")
    if not name:
        report.errors.append("Collection missing 'name', skipped.")
        return

    # Resolve source slugs -> IDs
    filter_source_ids: list[int] | None = None
    raw_source_slugs: list[str | None] | None = raw.get("filter_source_slugs")
    if raw_source_slugs is not None:
        resolved_ids = []
        for slug in raw_source_slugs:
            if slug is None:
                report.warnings.append(
                    f"Collection '{name}': unresolved source reference (None slug), skipped."
                )
                report.collections_skipped += 1
                return
            sid = source_slug_to_id.get(slug)
            if sid is None:
                report.warnings.append(
                    f"Collection '{name}': source '{slug}' not found in DB after import, skipped."
                )
                report.collections_skipped += 1
                return
            resolved_ids.append(sid)
        filter_source_ids = resolved_ids or None

    # Resolve feed refs -> IDs
    filter_feed_ids: list[int] | None = None
    raw_feed_refs: list[dict | None] | None = raw.get("filter_feed_refs")
    if raw_feed_refs is not None:
        resolved_feed_ids = []
        for ref in raw_feed_refs:
            if ref is None:
                report.warnings.append(
                    f"Collection '{name}': unresolved feed reference (None ref), skipped."
                )
                report.collections_skipped += 1
                return
            key = (ref.get("source_slug", ""), ref.get("feed_url", ""))
            fid = feed_ref_to_id.get(key)
            if fid is None:
                report.warnings.append(
                    f"Collection '{name}': feed '{key}' not found in DB after import, skipped."
                )
                report.collections_skipped += 1
                return
            resolved_feed_ids.append(fid)
        filter_feed_ids = resolved_feed_ids or None

    existing = session.exec(select(Collection).where(Collection.name == name)).first()

    if existing:
        if params.conflict_strategy == ConflictStrategy.SKIP:
            report.collections_skipped += 1
            return
        existing.filter_source_ids = filter_source_ids
        existing.filter_feed_ids = filter_feed_ids
        existing.filter_tags = raw.get("filter_tags")
        existing.filter_operator = raw.get("filter_operator", existing.filter_operator)
        existing.color = raw.get("color", existing.color)
        session.add(existing)
        session.flush()
        report.collections_skipped += 1
        return

    col_data = {
        k: v
        for k, v in raw.items()
        if k not in ("filter_source_slugs", "filter_feed_refs")
    }
    col_data["filter_source_ids"] = filter_source_ids
    col_data["filter_feed_ids"] = filter_feed_ids
    col = Collection(**col_data)
    session.add(col)
    session.flush()
    report.collections_created += 1
