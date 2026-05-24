"""Application settings loaded from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings

__all__ = ["Settings", "settings"]


class Settings(BaseSettings):
    """Central configuration for the MAPrompt Cards application.

    Every field can be overridden via an environment variable prefixed with
    ``MAP_`` (e.g. ``MAP_DB_PATH=prod.db``).
    """

    app_name: str = "MAPrompt Cards"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    db_path: str = "data/map_cards.db"

    # Cards directory
    cards_dir: str = "cards"

    # Schema path
    schema_path: str = "schemas/card-schema.json"

    # API
    api_prefix: str = "/api"

    model_config = {"env_prefix": "MAP_"}

    @property
    def database_url(self) -> str:
        """Build the SQLAlchemy database URL, creating parent dirs as needed."""
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"


settings = Settings()
