# app/core/tags.py

import re


def normalize_tag(tag: str) -> str:
    """Normalize a tag to a consistent format.
    - lowercase
    - strip whitespace
    - replace spaces/underscores with hyphens
    - remove special characters

    Args:
        tag (str): Tag to normalize.

    Returns:
        str: Normalized tag.
    """
    tag = tag.lower().strip()
    tag = re.sub(r"[\s_]+", "-", tag)
    tag = re.sub(r"[^\w-]", "", tag)
    return tag


def normalize_tags(tags: list[str]) -> list[str]:
    """Normalize and deduplicate a list of tags.

    Args:
        tags (list[str]): Tags to normalize.

    Returns:
        list[str]: Normalized tags.
    """
    seen = set()
    result = []
    for tag in tags:
        normalized = normalize_tag(tag)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
