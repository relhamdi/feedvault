from datetime import UTC, datetime

from sqlalchemy import event
from sqlmodel import Field, SQLModel


class TimestampModel(SQLModel):
    """Base class that auto-updates updated_at on every change."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def _update_timestamp(mapper, connection, target):
    if hasattr(target, "updated_at"):
        target.updated_at = datetime.now(UTC)


# Register the listener for all subclasses
@event.listens_for(TimestampModel, "before_update", propagate=True)
def before_update(mapper, connection, target):
    _update_timestamp(mapper, connection, target)
