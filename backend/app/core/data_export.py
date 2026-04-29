from app.core.crypto import decrypt_credentials
from app.models.author import Author
from app.models.category import Category
from app.models.collection import Collection
from app.models.export import (
    EXCLUDE_AUTHOR,
    EXCLUDE_CATEGORY,
    EXCLUDE_FEED,
    EXCLUDE_ITEM,
    EXCLUDE_MEDIA,
    EXCLUDE_SOURCE,
    ExportOptions,
)
from app.models.feed import Feed
from app.models.item import Item
from app.models.item_media import ItemMedia
from app.models.source import Source


def serialize_author(author: Author) -> dict:
    return author.model_dump(exclude=EXCLUDE_AUTHOR)


def serialize_media(media: ItemMedia) -> dict:
    return media.model_dump(exclude=EXCLUDE_MEDIA)


def serialize_category(cat: Category, cat_index: dict[int, Category]) -> dict:
    d = cat.model_dump(exclude=EXCLUDE_CATEGORY)
    # Resolve parent_id -> parent_name (portable across instances)
    parent_name: str | None = None
    if cat.parent_id is not None:
        parent = cat_index.get(cat.parent_id)
        parent_name = parent.name if parent else None
    d["parent_name"] = parent_name
    return d


def serialize_item(
    item: Item,
    cat_index: dict[int, Category],
    options: ExportOptions,
) -> dict:
    d = item.model_dump(exclude=EXCLUDE_ITEM)

    # Conditional personal fields
    if not options.include_read_status:
        d.pop("is_read", None)
    if not options.include_favorites:
        d.pop("is_favorite", None)

    # Inline relations (already loaded via selectinload on the query side)
    d["author"] = serialize_author(item.author) if item.author else None
    d["categories"] = [serialize_category(c, cat_index) for c in item.categories]
    d["media"] = [serialize_media(m) for m in item.media]

    return d


def serialize_feed(
    feed: Feed,
    items: list[Item],
    cat_index: dict[int, Category],
    options: ExportOptions,
) -> dict:
    d = feed.model_dump(exclude=EXCLUDE_FEED)
    d["items"] = [serialize_item(item, cat_index, options) for item in items]
    return d


def serialize_source(
    source: Source,
    feeds_items: list[tuple[Feed, list[Item]]],
    cat_index: dict[int, Category],
    options: ExportOptions,
) -> dict:
    d = source.model_dump(exclude=EXCLUDE_SOURCE)

    # Credentials: opt-in, exported decrypted (plain dict) for cross-instance portability
    if options.include_credentials and source.credentials:
        try:
            d["credentials"] = decrypt_credentials(source.credentials)
        except Exception:
            d["credentials"] = None
    else:
        d["credentials"] = None

    d["feeds"] = [
        serialize_feed(feed, items, cat_index, options) for feed, items in feeds_items
    ]
    return d


def serialize_collection(
    collection: Collection,
    source_id_to_slug: dict[int, str],
    feed_id_to_ref: dict[int, dict[str, str]],
) -> dict:
    """
    Convert internal integer IDs to portable string references.
    If a referenced source/feed is not in the export selection maps, we still
    include the reference (as None slug/url) so the importer can emit a warning.
    """
    d = collection.model_dump(exclude={"id", "filter_source_ids", "filter_feed_ids"})

    # Resolve source IDs -> slugs
    if collection.filter_source_ids:
        d["filter_source_slugs"] = [
            source_id_to_slug.get(sid)  # None if not in selection
            for sid in collection.filter_source_ids
        ]
    else:
        d["filter_source_slugs"] = None

    # Resolve feed IDs -> {source_slug, feed_url}
    if collection.filter_feed_ids:
        d["filter_feed_refs"] = [
            feed_id_to_ref.get(fid)  # None if not in selection
            for fid in collection.filter_feed_ids
        ]
    else:
        d["filter_feed_refs"] = None

    return d
