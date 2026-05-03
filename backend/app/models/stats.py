from pydantic import BaseModel


class GlobalStats(BaseModel):
    sources: int
    feeds: int
    items: int
    unread: int
    favorite: int


class FeedStats(BaseModel):
    total: int
    unread: int
    favorite: int
    nsfw: int
    not_public: int


class SourceStats(FeedStats):
    feeds_count: int
    active_feeds_count: int


class CollectionStats(BaseModel):
    total: int
    unread: int
