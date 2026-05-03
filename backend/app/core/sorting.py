from enum import Enum


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SourceSortField(str, Enum):
    NAME = "name"
    LAST_SCRAPED_AT = "last_scraped_at"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    IS_ACTIVE = "is_active"


class FeedSortField(str, Enum):
    NAME = "name"
    LAST_SCRAPED_AT = "last_scraped_at"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    IS_ACTIVE = "is_active"


class ItemSortField(str, Enum):
    SOURCE_PUBLISHED_AT = "source_published_at"
    SOURCE_UPDATED_AT = "source_updated_at"
    SCRAPED_AT = "scraped_at"
    LAST_SCRAPED_AT = "last_scraped_at"
