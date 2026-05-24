"""Application settings using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MAPrompt Cards application settings."""

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
        """Get SQLAlchemy database URL."""
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"


settings = Settings()
