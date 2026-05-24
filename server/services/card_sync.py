"""Sync YAML card files from the cards/ directory into the database."""

import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import yaml
from sqlalchemy.orm import Session

from server.db.models import Card
from server.settings import settings


def load_schema() -> dict:
    """Load the card JSON Schema."""
    schema_path = Path(settings.schema_path)
    if schema_path.exists():
        return json.loads(schema_path.read_text())
    return {}


def validate_card_data(data: dict, schema: dict) -> list[str]:
    """Validate card data against the JSON Schema. Returns list of errors."""
    errors = []
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        errors.append(str(e.message))
    except jsonschema.SchemaError as e:
        errors.append(f"Schema error: {e.message}")
    return errors


def parse_date(date_str: str | None) -> datetime:
    """Parse a date string into a datetime object."""
    if date_str:
        try:
            return datetime.strptime(str(date_str), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def sync_cards_from_directory(db: Session, cards_dir: str | None = None) -> dict:
    """Walk cards/ directory, parse each card.yaml, upsert into DB.

    Returns a summary dict with counts of synced, skipped, and errored cards.
    """
    cards_path = Path(cards_dir or settings.cards_dir)
    schema = load_schema()

    results = {"synced": 0, "skipped": 0, "errors": []}

    if not cards_path.exists():
        results["errors"].append(f"Cards directory not found: {cards_path}")
        return results

    for card_dir in sorted(cards_path.iterdir()):
        if not card_dir.is_dir():
            continue

        yaml_path = card_dir / "card.yaml"
        if not yaml_path.exists():
            results["skipped"] += 1
            continue

        try:
            data = yaml.safe_load(yaml_path.read_text())
            if not data:
                results["errors"].append(f"{card_dir.name}: Empty YAML file")
                continue

            # Validate against schema
            if schema:
                errors = validate_card_data(data, schema)
                if errors:
                    results["errors"].append(f"{card_dir.name}: {'; '.join(errors)}")
                    continue

            # Upsert card
            existing = db.query(Card).filter(Card.name == data["name"]).first()

            if existing:
                # Update existing card
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
                existing.license = data.get("license", "MIT")
                existing.updated_at = parse_date(data.get("updated_at"))
            else:
                # Create new card
                card = Card(
                    name=data["name"],
                    title=data.get("title", data["name"]),
                    description=data.get("description", ""),
                    author=data.get("author", "anonymous"),
                    author_url=data.get("author_url", ""),
                    category=data.get("category", "uncategorized"),
                    tags=data.get("tags", []),
                    platforms=data.get("platforms", []),
                    prompt=data.get("prompt", ""),
                    variables=data.get("variables", []),
                    version=data.get("version", "1.0.0"),
                    license=data.get("license", "MIT"),
                    created_at=parse_date(data.get("created_at")),
                    updated_at=parse_date(data.get("updated_at")),
                )
                db.add(card)

            results["synced"] += 1

        except yaml.YAMLError as e:
            results["errors"].append(f"{card_dir.name}: YAML parse error: {e}")
        except Exception as e:
            results["errors"].append(f"{card_dir.name}: {e}")

    db.commit()
    return results
