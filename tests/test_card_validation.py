"""Tests for card YAML validation against the JSON Schema."""

import json
import sys
from pathlib import Path

import yaml

from server.services.card_sync import validate_card_data


def test_all_cards_are_valid_yaml():
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

    assert count >= 9, f"Expected at least 9 cards, found {count}"
    print(f"  PASS: {count} cards are valid YAML")


def test_all_cards_match_schema():
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

    print("  PASS: All cards match the JSON Schema")


def test_card_names_match_directories():
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

    print("  PASS: All card names match their directory names")


def test_required_fields_present():
    """Every card must have all required fields."""
    required = ["name", "version", "title", "description", "author", "category", "tags", "platforms", "prompt"]
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

    print("  PASS: All cards have required fields")


def test_prompts_are_substantial():
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
        assert len(prompt) >= 100, (
            f"{card_dir.name}: prompt is too short ({len(prompt)} chars). "
            "Expected at least 100 characters of real content."
        )

    print("  PASS: All prompts are substantial (>=100 chars)")


def test_invalid_card_fails_validation():
    """An invalid card should fail schema validation."""
    schema_path = Path("schemas/card-schema.json")
    schema = json.loads(schema_path.read_text())

    invalid_card = {"name": "x", "title": "ab"}  # Missing required fields, name too short
    errors = validate_card_data(invalid_card, schema)
    assert len(errors) > 0, "Invalid card should fail validation"
    print("  PASS: Invalid cards are correctly rejected")


def main():
    print("\nTest: Card Validation")
    print("=" * 40)
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
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
