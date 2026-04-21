from pydantic import BaseModel


class FeedStats(BaseModel):
    total: int
    unread: int
    favorite: int
    nsfw: int
    not_public: int


class SourceStats(FeedStats):
    feeds_count: int
    active_feeds_count: int
