from fastapi import APIRouter

from app.api.v1 import authors, categories, collections, feeds, items, sources

router = APIRouter()
router.include_router(sources.router, prefix="/sources", tags=["sources"])
router.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
router.include_router(authors.router, prefix="/authors", tags=["authors"])
router.include_router(categories.router, prefix="/categories", tags=["categories"])
router.include_router(items.router, prefix="/items", tags=["items"])
router.include_router(collections.router, prefix="/collections", tags=["collections"])
