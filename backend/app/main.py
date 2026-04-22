from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlmodel import Session

from app.api.v1.router import router as v1_router
from app.config import settings
from app.database import get_session

app = FastAPI(
    title="FeedVault",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")

media_path = Path(settings.media_dir)
media_path.mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=media_path), name="media")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/pragma")
def check_pragma(session: Session = Depends(get_session)):
    result = session.exec(text("PRAGMA foreign_keys")).first()  # type: ignore
    return {"foreign_keys": result[0]}
