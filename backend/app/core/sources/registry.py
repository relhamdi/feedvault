from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from app.core.sources.base import BaseSource

ScraperClass = type["BaseSource"]


@dataclass
class ScraperRegistration:
    slug: str
    cls: ScraperClass
    # Optional metadata for POST /sources/bootstrap — unused if empty
    default_source: dict = field(default_factory=dict)


_REGISTRY: dict[str, ScraperRegistration] = {}


def register_scraper(slug: str, *, default_source: dict | None = None) -> Callable:
    """Decorator — registers a scraper based on a slug.

    Ex:
    @register_scraper("gamebanana", default_source={
        "name": "Gamebanana",
        "source_type": "API",
        "base_url": "https://gamebanana.com/apiv8",
        "color": "#D2BC2B",
        "icon_path": "https://images.gamebanana.com/static/img/banana.png",
    })
    """

    def decorator(cls: ScraperClass) -> ScraperClass:
        _REGISTRY[slug] = ScraperRegistration(
            slug=slug,
            cls=cls,
            default_source=default_source or {},
        )
        return cls

    return decorator


def get_scraper_class(slug: str) -> ScraperClass | None:
    """Get scraper class registered for a given slug.

    Args:
        slug (str): Scraper slug.

    Returns:
        ScraperClass | None: Scraper class if slug is registered, else None.
    """
    reg = _REGISTRY.get(slug)
    return reg.cls if reg else None


def get_registration(slug: str) -> ScraperRegistration | None:
    """Get the full registration entry for a given slug, if registered.

    Args:
        slug (str): Scraper slug.

    Returns:
        ScraperRegistration | None: Registration if found, else None.
    """
    return _REGISTRY.get(slug)


def registered_slugs() -> list[str]:
    """List registered slugs.

    Returns:
        list[str]: Slug list.
    """
    return list(_REGISTRY.keys())
