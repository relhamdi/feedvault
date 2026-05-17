from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image
from sqlmodel import Session, col, select

from app.config import settings
from app.core.constants import THUMBNAIL_MAX_SIZE, THUMBNAIL_QUALITY
from app.models.feed import Feed
from app.models.item import Item


def download_and_compress(url: str, dest: Path) -> bool:
    """Download a remote image, compresses it to WebP, and saves it.

    Args:
        url (str): File to download
        dest (Path): Save path.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url)
            response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        image.thumbnail(THUMBNAIL_MAX_SIZE, Image.Resampling.LANCZOS)

        dest.parent.mkdir(parents=True, exist_ok=True)
        image.save(dest, format="WEBP", quality=THUMBNAIL_QUALITY)
        return True

    except Exception:
        return False


def download_and_compress_batch(
    tasks: list[tuple[str, Path]],
    max_workers: int = 6,
) -> tuple[int, int]:
    """Download and compress multiple images in parallel.

    Args:
        tasks (list[tuple[str, Path]]): List of (url, dest_path) tuples.
        max_workers (int, optional): Number of workers.
            Defaults to 6.

    Returns:
        tuple[int, int]: Tuple (success_count, failure_count).
    """
    if not tasks:
        return 0, 0

    success = 0
    failure = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_and_compress, url, dest): (url, dest)
            for url, dest in tasks
        }
        for future in as_completed(futures):
            if future.result():
                success += 1
            else:
                failure += 1

    return success, failure


def get_thumbnail_path(
    source_slug: str,
    external_id: str,
    sub_path: str | None = None,
) -> Path:
    """Return the local WebP path for an item.

    Args:
        source_slug (str): Source slug.
        external_id (str): Item ID.
        sub_path (str | None, optional): Optional sub path for the thumbnail.
            Defaults to None.

    Returns:
        Path: Local path for the item.
    """
    media_dir = Path(settings.media_dir)
    if sub_path:
        return media_dir / source_slug / sub_path / f"{external_id}.webp"
    return media_dir / source_slug / f"{external_id}.webp"


def delete_thumbnail(thumbnail_path: str | None) -> None:
    """Delete a local thumbnail file if it exists."""
    if not thumbnail_path:
        return

    try:
        dest = Path(settings.media_dir) / thumbnail_path
        dest.unlink(missing_ok=True)
    except Exception:
        pass


def delete_thumbnail_files(paths: list[str]) -> None:
    for path in paths:
        delete_thumbnail(path)


def get_thumbnail_paths_for_feed(session: Session, feed_id: int) -> list[str]:
    paths = session.exec(
        select(Item.thumbnail_path).where(
            Item.feed_id == feed_id, col(Item.thumbnail_path).is_not(None)
        )
    ).all()
    return [p for p in paths if p is not None]


def get_thumbnail_paths_for_source(session: Session, source_id: int) -> list[str]:
    feed_ids = session.exec(select(Feed.id).where(Feed.source_id == source_id)).all()
    if not feed_ids:
        return []

    paths = session.exec(
        select(Item.thumbnail_path).where(
            col(Item.feed_id).in_(feed_ids), col(Item.thumbnail_path).is_not(None)
        )
    ).all()
    return [p for p in paths if p is not None]
