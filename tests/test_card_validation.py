"""Tests for card YAML validation against the JSON Schema."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import yaml

from map_cards.services.card_sync import validate_card_data

logger = logging.getLogger(__name__)

_MIN_CARD_COUNT = 9
_MIN_PROMPT_LENGTH = 100


def test_all_cards_are_valid_yaml() -> None:
    """Every card.yaml file must be parseable YAML."""
    cards_dir = Path("cards")
    assert cards_dir.exists(), "cards/ directory not found"

    count = 0
    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        yaml_path = card_dir / "card.yaml"
        assert yaml_path.exists(), f"Missing card.yaml in {card_dir.name}"

        data = yaml.safe_load(yaml_path.read_text())
        assert data is not None, f"Empty card.yaml in {card_dir.name}"
        assert isinstance(data, dict), f"card.yaml in {card_dir.name} is not a mapping"
        count += 1

    assert count >= _MIN_CARD_COUNT, f"Expected at least {_MIN_CARD_COUNT} cards, found {count}"
    logger.info("  PASS: %d cards are valid YAML", count)


def test_all_cards_match_schema() -> None:
    """Every card.yaml must validate against the JSON Schema."""
    schema_path = Path("schemas/card-schema.json")
    assert schema_path.exists(), "schemas/card-schema.json not found"

    schema = json.loads(schema_path.read_text())
    cards_dir = Path("cards")

    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        yaml_path = card_dir / "card.yaml"
        if not yaml_path.exists():
            continue

        data = yaml.safe_load(yaml_path.read_text())
        errors = validate_card_data(data, schema)
        assert not errors, f"{card_dir.name} failed validation: {errors}"

    logger.info("  PASS: All cards match the JSON Schema")


def test_card_names_match_directories() -> None:
    """The 'name' field in each card.yaml must match its directory name."""
    cards_dir = Path("cards")

    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        yaml_path = card_dir / "card.yaml"
        if not yaml_path.exists():
            continue

        data = yaml.safe_load(yaml_path.read_text())
        assert data["name"] == card_dir.name, (
            f"Card name '{data['name']}' does not match directory '{card_dir.name}'"
        )

    logger.info("  PASS: All card names match their directory names")


def test_required_fields_present() -> None:
    """Every card must have all required fields."""
    required = [
        "name", "version", "title", "description", "author",
        "category", "tags", "platforms", "prompt",
    ]
    cards_dir = Path("cards")

    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        yaml_path = card_dir / "card.yaml"
        if not yaml_path.exists():
            continue

        data = yaml.safe_load(yaml_path.read_text())
        for field in required:
            assert field in data, f"{card_dir.name}: missing required field '{field}'"
            assert data[field], f"{card_dir.name}: empty required field '{field}'"

    logger.info("  PASS: All cards have required fields")


def test_prompts_are_substantial() -> None:
    """Prompts should be real content, not placeholders."""
    cards_dir = Path("cards")

    for card_dir in sorted(cards_dir.iterdir()):
        if not card_dir.is_dir():
            continue
        yaml_path = card_dir / "card.yaml"
        if not yaml_path.exists():
            continue

        data = yaml.safe_load(yaml_path.read_text())
        prompt = data.get("prompt", "")
        assert len(prompt) >= _MIN_PROMPT_LENGTH, (
            f"{card_dir.name}: prompt is too short ({len(prompt)} chars). "
            f"Expected at least {_MIN_PROMPT_LENGTH} characters of real content."
        )

    logger.info("  PASS: All prompts are substantial (>=%d chars)", _MIN_PROMPT_LENGTH)


def test_invalid_card_fails_validation() -> None:
    """An invalid card should fail schema validation."""
    schema_path = Path("schemas/card-schema.json")
    schema = json.loads(schema_path.read_text())

    invalid_card = {"name": "x", "title": "ab"}  # Missing required fields
    errors = validate_card_data(invalid_card, schema)
    assert len(errors) > 0, "Invalid card should fail validation"
    logger.info("  PASS: Invalid cards are correctly rejected")


def main() -> None:
    """Run all card validation tests."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("\nTest: Card Validation")
    logger.info("=" * 40)

    tests = [
        test_all_cards_are_valid_yaml,
        test_all_cards_match_schema,
        test_card_names_match_directories,
        test_required_fields_present,
        test_prompts_are_substantial,
        test_invalid_card_fails_validation,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as exc:
            logger.error("  FAIL: %s: %s", test.__name__, exc)
            failed += 1
        except Exception as exc:
            logger.error("  ERROR: %s: %s", test.__name__, exc)
            failed += 1

    logger.info("\n%d passed, %d failed", passed, failed)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
