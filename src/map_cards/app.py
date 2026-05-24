"""FastAPI application factory for MAPrompt Cards."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from map_cards.api import analytics, cards, downloads, ratings
from map_cards.config import settings
from map_cards.database import create_tables

__all__ = ["create_app", "app"]


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

    @application.get("/")
    def _root():  # type: ignore[return]
        """Serve the dashboard HTML when available, otherwise return API info."""
        index_path = Path("web/index.html")
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        return {"message": "MAPrompt Cards API", "docs": "/docs"}

    return application


# Module-level instance for ``uvicorn map_cards.app:app``.
app = create_app()
