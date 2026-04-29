from enum import Enum

from pydantic import BaseModel

# Schema version
CURRENT_EXPORT_SCHEMA_VERSION = "1.0"
SUPPORTED_IMPORT_VERSIONS = ["1.0"]


# Fields excluded from model_dump() at each level
EXCLUDE_SOURCE: set[str] = {"id", "credentials"}
EXCLUDE_FEED: set[str] = {"id", "source_id"}
EXCLUDE_ITEM: set[str] = {"id", "feed_id", "author_id"}
EXCLUDE_AUTHOR: set[str] = {"id", "source_id"}
EXCLUDE_CATEGORY: set[str] = {"id", "source_id", "parent_id"}
EXCLUDE_MEDIA: set[str] = {"id", "item_id"}


class ExportSelection(BaseModel):
    """
    Hierarchical selection for export.
    - feed_ids: export ALL items of these feeds
    - collection_ids: collections to include (parent feeds/sources auto-included in the collection block;
        their items are NOT exported unless also selected through the feeds)
    Passing no filter at all (all empty lists) -> full export.
    """

    feed_ids: list[int] = []
    collection_ids: list[int] = []


class ExportOptions(BaseModel):
    include_credentials: bool = False
    include_read_status: bool = True
    include_favorites: bool = True
    include_collections: bool = True


class ConflictStrategy(str, Enum):
    UPSERT = "upsert"
    SKIP = "skip"


class ImportParams(BaseModel):
    conflict_strategy: ConflictStrategy = ConflictStrategy.UPSERT
    redownload_missing_images: bool = False


class ImportReport(BaseModel):
    success: bool = False
    sources_created: int = 0
    sources_skipped: int = 0
    feeds_created: int = 0
    feeds_skipped: int = 0
    items_created: int = 0
    items_updated: int = 0
    items_skipped: int = 0
    collections_created: int = 0
    collections_skipped: int = 0
    images_downloaded: int = 0
    images_failed: int = 0
    errors: list[str] = []
    warnings: list[str] = []
