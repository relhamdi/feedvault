from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image

from app.config import settings
from app.core.constants import THUMBNAIL_MAX_SIZE, THUMBNAIL_QUALITY


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
