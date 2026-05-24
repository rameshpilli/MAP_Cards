"""Sync YAML card files from the cards/ directory into the database."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import yaml
from sqlalchemy.orm import Session

from map_cards.config import settings
from map_cards.models import Card

__all__ = ["sync_cards_from_directory", "validate_card_data"]

logger = logging.getLogger(__name__)

# Defaults applied when a YAML field is absent.
_DEFAULT_VERSION = "1.0.0"
_DEFAULT_LICENSE = "MIT"
_DEFAULT_AUTHOR = "anonymous"
_DEFAULT_CATEGORY = "uncategorized"


def load_schema() -> dict:
    """Load the card JSON Schema from disk.

    Returns an empty dict if the file is missing so callers can skip validation.
    """
    schema_path = Path(settings.schema_path)
    if schema_path.exists():
        return json.loads(schema_path.read_text())
    return {}


def validate_card_data(data: dict, schema: dict) -> list[str]:
    """Validate *data* against *schema*.  Returns a list of error messages."""
    errors: list[str] = []
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        errors.append(str(exc.message))
    except jsonschema.SchemaError as exc:
        errors.append(f"Schema error: {exc.message}")
    return errors


def _parse_date(date_str: str | None) -> datetime:
    """Parse a ``YYYY-MM-DD`` string into a UTC datetime, falling back to *now*."""
    if date_str:
        try:
            return datetime.strptime(str(date_str), "%Y-%m-%d").replace(
                tzinfo=timezone.utc,
            )
        except ValueError:
            logger.warning("Unparseable date '%s'; using current time", date_str)
    return datetime.now(timezone.utc)


def sync_cards_from_directory(
    db: Session,
    cards_dir: str | None = None,
    *,
    prune_missing: bool = False,
) -> dict[str, int | list[str]]:
    """Walk the cards directory, parse each ``card.yaml``, and upsert into the DB.

    When ``prune_missing`` is true, cards not present on disk are removed from the DB.

    Returns ``{"synced": int, "skipped": int, "pruned": int, "errors": [str, ...]}``.
    """
    cards_path = Path(cards_dir or settings.cards_dir)
    schema = load_schema()

    results: dict[str, int | list[str]] = {
        "synced": 0,
        "skipped": 0,
        "pruned": 0,
        "errors": [],
    }
    seen_names: set[str] = set()

    if not cards_path.exists():
        results["errors"].append(f"Cards directory not found: {cards_path}")  # type: ignore[union-attr]
        return results

    for card_dir in sorted(cards_path.iterdir()):
        if not card_dir.is_dir():
            continue

        yaml_path = card_dir / "card.yaml"
        if not yaml_path.exists():
            results["skipped"] += 1  # type: ignore[operator]
            continue

        try:
            data = yaml.safe_load(yaml_path.read_text())
            if not data:
                results["errors"].append(f"{card_dir.name}: Empty YAML file")  # type: ignore[union-attr]
                continue

            seen_names.add(data["name"])

            # Validate against schema
            if schema:
                errors = validate_card_data(data, schema)
                if errors:
                    results["errors"].append(  # type: ignore[union-attr]
                        f"{card_dir.name}: {'; '.join(errors)}",
                    )
                    continue

            # Upsert card
            existing = db.query(Card).filter(Card.name == data["name"]).first()

            if existing:
                existing.title = data.get("title", existing.title)
                existing.description = data.get("description", existing.description)
                existing.author = data.get("author", existing.author)
                existing.author_url = data.get("author_url", "")
                existing.category = data.get("category", existing.category)
                existing.tags = data.get("tags", existing.tags)
                existing.platforms = data.get("platforms", existing.platforms)
                existing.prompt = data.get("prompt", existing.prompt)
                existing.variables = data.get("variables", existing.variables)
                existing.version = data.get("version", existing.version)
                existing.license = data.get("license", _DEFAULT_LICENSE)
                existing.updated_at = _parse_date(data.get("updated_at"))
            else:
                card = Card(
                    name=data["name"],
                    title=data.get("title", data["name"]),
                    description=data.get("description", ""),
                    author=data.get("author", _DEFAULT_AUTHOR),
                    author_url=data.get("author_url", ""),
                    category=data.get("category", _DEFAULT_CATEGORY),
                    tags=data.get("tags", []),
                    platforms=data.get("platforms", []),
                    prompt=data.get("prompt", ""),
                    variables=data.get("variables", []),
                    version=data.get("version", _DEFAULT_VERSION),
                    license=data.get("license", _DEFAULT_LICENSE),
                    created_at=_parse_date(data.get("created_at")),
                    updated_at=_parse_date(data.get("updated_at")),
                )
                db.add(card)

            results["synced"] += 1  # type: ignore[operator]

        except yaml.YAMLError as exc:
            results["errors"].append(f"{card_dir.name}: YAML parse error: {exc}")  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            results["errors"].append(f"{card_dir.name}: {exc}")  # type: ignore[union-attr]

    if prune_missing and seen_names:
        stale_cards = db.query(Card).filter(~Card.name.in_(seen_names)).all()
        for stale_card in stale_cards:
            db.delete(stale_card)
        results["pruned"] = len(stale_cards)  # type: ignore[assignment]

    db.commit()
    return results
