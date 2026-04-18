from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.image import download_and_compress, get_thumbnail_path
from app.core.sources.models import NormalizedItem, RawAuthor, RawCategory, RawMedia
from app.models.author import Author
from app.models.category import Category
from app.models.feed import Feed
from app.models.item import Item
from app.models.item_media import ItemMedia, MediaType
from app.models.links import ItemCategoryLink


def _upsert_author(session: Session, raw: RawAuthor, source_id: int) -> Author:
    author = session.exec(
        select(Author).where(
            Author.external_id == raw.external_id,
            Author.source_id == source_id,
        )
    ).first()

    if not author:
        author = Author(
            external_id=raw.external_id,
            source_id=source_id,
            name=raw.name,
            url=raw.url,
            icon_url=raw.icon_url,
        )
    else:
        author.name = raw.name
        author.url = raw.url
        author.icon_url = raw.icon_url

    session.add(author)
    session.flush()
    return author


def _upsert_category(
    session: Session,
    raw: RawCategory,
    source_id: int,
    parent: Category | None = None,
) -> Category:
    category = session.exec(
        select(Category).where(
            Category.name == raw.name,
            Category.source_id == source_id,
            Category.parent_id == (parent.id if parent else None),
        )
    ).first()

    if not category:
        category = Category(
            name=raw.name,
            source_id=source_id,
            parent_id=parent.id if parent else None,
        )
    else:
        category.name = raw.name
        category.parent_id = parent.id if parent else None

    session.add(category)
    session.flush()
    return category


def _upsert_categories(
    session: Session,
    raw_categories: list[RawCategory],
    source_id: int,
) -> list[Category]:
    """
    Resolve the parent-child hierarchy and inserts elements in order.
    Handles any number of nesting levels by processing nodes whose parent is already resolved before others.
    """
    resolved: dict[str, Category] = {}
    pending = list(raw_categories)
    max_iterations = len(pending) ** 2  # Guard against circular refs
    iterations = 0

    while pending:
        iterations += 1
        if iterations > max_iterations:
            raise RuntimeError("Circular reference detected in categories")

        raw = pending.pop(0)

        # If parent is expected but not yet resolved, defer
        if raw.parent_external_id and raw.parent_external_id not in resolved:
            pending.append(raw)
            continue

        parent = (
            resolved.get(raw.parent_external_id) if raw.parent_external_id else None
        )
        category = _upsert_category(session, raw, source_id, parent)
        resolved[raw.external_id] = category

    return list(resolved.values())


def _sync_media(session: Session, item: Item, raw_media: list[RawMedia]) -> None:
    """Replaces the item's existing media with the new media."""
    assert item.id is not None

    existing = session.exec(select(ItemMedia).where(ItemMedia.item_id == item.id)).all()
    for m in existing:
        session.delete(m)
    session.flush()

    for raw in raw_media:
        media = ItemMedia(
            item_id=item.id,
            media_type=MediaType(raw.media_type),
            url=raw.url,
            label=raw.label,
            mime_type=raw.mime_type,
            extra=raw.extra,
        )
        session.add(media)


def _sync_categories(
    session: Session,
    item: Item,
    categories: list[Category],
) -> None:
    """Replaces the item's existing category links."""
    assert item.id is not None

    existing = session.exec(
        select(ItemCategoryLink).where(ItemCategoryLink.item_id == item.id)
    ).all()
    for link in existing:
        session.delete(link)
    session.flush()

    for category in categories:
        session.add(ItemCategoryLink(item_id=item.id, category_id=category.id))


def upsert_item(
    session: Session,
    normalized: NormalizedItem,
    feed: Feed,
    source_slug: str,
) -> Item:
    assert feed.id is not None
    now = datetime.now(UTC)

    # --- Author ---
    author_id = None
    if normalized.author:
        author = _upsert_author(session, normalized.author, feed.source_id)
        author_id = author.id

    # --- Thumbnail ---
    thumbnail_path = None
    if normalized.thumbnail_url:
        dest = get_thumbnail_path(source_slug, normalized.external_id)
        if not dest.exists():
            success = download_and_compress(normalized.thumbnail_url, dest)
            if success:
                thumbnail_path = str(dest)
        else:
            thumbnail_path = str(dest)

    # --- Tags: custom + inherited from feed and source ---
    tags = list(set(normalized.tags + list(feed.default_tags or [])))

    # --- Item upsert ---
    item = session.exec(
        select(Item).where(
            Item.external_id == normalized.external_id,
            Item.feed_id == feed.id,
        )
    ).first()

    if not item:
        item = Item(
            feed_id=feed.id,
            author_id=author_id,
            external_id=normalized.external_id,
            title=normalized.title,
            url=normalized.url,
            description=normalized.description,
            summary=normalized.summary,
            thumbnail_path=thumbnail_path,
            tags=tags,
            stats=normalized.stats,
            raw_extra=normalized.raw_extra,
            is_nsfw=normalized.is_nsfw,
            is_public=normalized.is_public,
            source_published_at=normalized.source_published_at,
            source_updated_at=normalized.source_updated_at,
            scraped_at=now,
            last_scraped_at=now,
            last_seen_at=now,
        )
    else:
        item.title = normalized.title
        item.url = normalized.url
        item.description = normalized.description
        item.summary = normalized.summary
        item.tags = tags
        item.stats = normalized.stats
        item.raw_extra = normalized.raw_extra
        item.is_nsfw = normalized.is_nsfw
        item.is_public = normalized.is_public
        item.source_updated_at = normalized.source_updated_at
        item.last_scraped_at = now
        item.last_seen_at = now
        item.author_id = author_id
        if thumbnail_path:
            item.thumbnail_path = thumbnail_path

    session.add(item)
    session.flush()

    # --- Categories & Media ---
    categories = _upsert_categories(session, normalized.categories, feed.source_id)
    _sync_categories(session, item, categories)
    _sync_media(session, item, normalized.media)

    session.commit()
    session.refresh(item)
    return item
