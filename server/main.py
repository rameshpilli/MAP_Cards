"""FastAPI application for MAPrompt Cards marketplace."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.api import analytics, cards, downloads, ratings
from server.db.base import create_tables
from server.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A public marketplace for reusable AI prompt templates",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(cards.router, prefix=settings.api_prefix)
app.include_router(downloads.router, prefix=settings.api_prefix)
app.include_router(ratings.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)


@app.on_event("startup")
def on_startup():
    """Create database tables on startup."""
    create_tables()


@app.get("/")
def root():
    """Serve the dashboard HTML."""
    index_path = Path("client/index.html")
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    return {"message": "MAPrompt Cards API", "docs": "/docs"}
