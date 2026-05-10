from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlmodel import Session, case, func, select

from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.sources.models import ScrapeJobStatus
from app.database import engine, get_session
from app.models.feed import Feed
from app.models.item import Item
from app.models.scrape_job import ScrapeJobRecord
from app.models.source import Source
from app.models.stats import GlobalStats


def recover_stuck_jobs():
    with Session(engine) as session:
        stuck = session.exec(
            select(ScrapeJobRecord).where(
                ScrapeJobRecord.status == ScrapeJobStatus.RUNNING
            )
        ).all()
        for job in stuck:
            job.status = ScrapeJobStatus.ERROR
            job.error_message = "Job interrupted — server restarted"
            job.finished_at = datetime.now(UTC)
            session.add(job)
        session.commit()
        if stuck:
            print(f"Recovered {len(stuck)} stuck jobs")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    recover_stuck_jobs()
    yield
    # Shutdown


app = FastAPI(
    title="FeedVault",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    expose_headers=["Content-Disposition"],
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


@app.get("/stats", response_model=GlobalStats)
def global_stats(session: Session = Depends(get_session)):
    sources = session.exec(select(func.count(Source.id))).one()  # type: ignore
    feeds = session.exec(select(func.count(Feed.id))).one()  # type: ignore
    total, unread, favorite = session.exec(
        select(
            func.count(Item.id),  # type: ignore
            func.sum(case((~Item.is_read, 1), else_=0)),  # type: ignore
            func.sum(case((Item.is_favorite, 1), else_=0)),
        )
    ).one()
    return GlobalStats(
        sources=sources or 0,
        feeds=feeds or 0,
        items=total or 0,
        unread=unread or 0,
        favorite=favorite or 0,
    )


@app.get("/debug/pragma")
def check_pragma(session: Session = Depends(get_session)):
    result = session.exec(text("PRAGMA foreign_keys")).first()  # type: ignore
    return {"foreign_keys": result[0]}
