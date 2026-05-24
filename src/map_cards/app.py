"""FastAPI application factory for MAPrompt Cards."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from map_cards.api import analytics, cards, downloads, ratings
from map_cards.config import settings
from map_cards.database import SessionLocal, create_tables
from map_cards.services.card_sync import sync_cards_from_directory

__all__ = ["create_app", "app"]

logger = logging.getLogger(__name__)


def _web_dir() -> Path:
    """Resolve the bundled static frontend directory relative to the package."""
    return Path(__file__).resolve().parents[2] / "web"


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A public marketplace for reusable AI prompt templates",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(cards.router, prefix=settings.api_prefix)
    application.include_router(downloads.router, prefix=settings.api_prefix)
    application.include_router(ratings.router, prefix=settings.api_prefix)
    application.include_router(analytics.router, prefix=settings.api_prefix)

    @application.on_event("startup")
    def _on_startup() -> None:
        create_tables()
        db = SessionLocal()
        try:
            results = sync_cards_from_directory(db, prune_missing=True)
            if results["errors"]:
                logger.warning("Card sync completed with errors: %s", results["errors"])
        finally:
            db.close()

    web_dir = _web_dir()
    if web_dir.is_dir():
        application.mount(
            "/",
            StaticFiles(directory=web_dir, html=True),
            name="web",
        )
    else:
        @application.get("/")
        def _root() -> JSONResponse:
            """Fallback API response when the frontend bundle is unavailable."""
            return JSONResponse({"message": "MAPrompt Cards API", "docs": "/docs"})

    return application


# Module-level instance for ``uvicorn map_cards.app:app``.
app = create_app()
