"""Integration tests for the Cards API endpoints."""

from __future__ import annotations

import logging
import sys

from fastapi.testclient import TestClient

from map_cards.app import create_app
from map_cards.database import Base, SessionLocal, create_tables, engine
from map_cards.services.card_sync import sync_cards_from_directory

logger = logging.getLogger(__name__)

_MIN_CARD_COUNT = 9


def _setup() -> TestClient:
    """Reset the database, seed it from YAML files, and return a test client."""
    Base.metadata.drop_all(bind=engine)
    create_tables()
    db = SessionLocal()
    try:
        sync_cards_from_directory(db)
    finally:
        db.close()
    return TestClient(create_app())


def test_health() -> None:
    """Health endpoint should return healthy."""
    client = _setup()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    logger.info("  PASS: Health check")


def test_list_cards() -> None:
    """List cards should return all seeded cards."""
    client = _setup()
    resp = client.get("/api/cards")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= _MIN_CARD_COUNT, (
        f"Expected >= {_MIN_CARD_COUNT} cards, got {data['count']}"
    )
    assert len(data["cards"]) >= _MIN_CARD_COUNT
    logger.info("  PASS: List cards (%d cards)", data["count"])


def test_get_single_card() -> None:
    """Get a specific card by name."""
    client = _setup()
    resp = client.get("/api/cards/full-stack-code-review")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "full-stack-code-review"
    assert data["title"] == "Full-Stack Code Review Agent"
    assert len(data["prompt"]) > 100
    logger.info("  PASS: Get single card")


def test_get_card_not_found() -> None:
    """Getting a non-existent card should return 404."""
    client = _setup()
    resp = client.get("/api/cards/nonexistent-card")
    assert resp.status_code == 404
    logger.info("  PASS: Card not found returns 404")


def test_search_cards() -> None:
    """Search should filter cards by query."""
    client = _setup()
    resp = client.get("/api/cards?q=security")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1, "Expected at least 1 security-related card"
    for card in data["cards"]:
        text = (card["title"] + card["description"] + card["name"]).lower()
        assert "security" in text or "adversarial" in text, (
            f"Card {card['name']} doesn't match 'security'"
        )
    logger.info("  PASS: Search cards (%d results for 'security')", data["count"])


def test_filter_by_category() -> None:
    """Category filter should work."""
    client = _setup()
    resp = client.get("/api/cards?category=research")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    for card in data["cards"]:
        assert card["category"] == "research"
    logger.info("  PASS: Filter by category (%d research cards)", data["count"])


def test_sort_by_newest() -> None:
    """Sort by newest should work."""
    client = _setup()
    resp = client.get("/api/cards?sort=newest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 2
    dates = [c["created_at"] for c in data["cards"]]
    assert dates == sorted(dates, reverse=True), "Cards not sorted by newest"
    logger.info("  PASS: Sort by newest")


def test_download_card() -> None:
    """Downloading a card should increment count and return prompt."""
    client = _setup()
    resp = client.post("/api/cards/full-stack-code-review/download")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "full-stack-code-review"
    assert len(data["prompt"]) > 100
    assert data["download_count"] >= 1
    logger.info("  PASS: Download card (count: %d)", data["download_count"])


def test_rate_card() -> None:
    """Rating a card should update its average."""
    client = _setup()
    resp = client.post(
        "/api/cards/full-stack-code-review/rate",
        json={"user_id": "test-user-1", "stars": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["your_rating"] == 5
    assert data["avg_rating"] > 0
    assert data["rating_count"] >= 1
    logger.info("  PASS: Rate card (avg: %s, count: %d)", data["avg_rating"], data["rating_count"])


def test_rate_card_update() -> None:
    """Re-rating should update existing rating."""
    client = _setup()
    client.post(
        "/api/cards/full-stack-code-review/rate",
        json={"user_id": "test-user-update", "stars": 2},
    )
    resp = client.post(
        "/api/cards/full-stack-code-review/rate",
        json={"user_id": "test-user-update", "stars": 4},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["your_rating"] == 4
    logger.info("  PASS: Update existing rating")


def test_rate_card_invalid() -> None:
    """Rating with invalid stars should fail."""
    client = _setup()
    resp = client.post(
        "/api/cards/full-stack-code-review/rate",
        json={"user_id": "test-user-invalid", "stars": 6},
    )
    assert resp.status_code == 422
    logger.info("  PASS: Invalid rating rejected")


def test_trending_cards() -> None:
    """Trending endpoint should return cards."""
    client = _setup()
    resp = client.get("/api/cards/trending?limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["cards"]) <= 3
    logger.info("  PASS: Trending cards (%d returned)", len(data["cards"]))


def test_categories() -> None:
    """Categories endpoint should return categories with counts."""
    client = _setup()
    resp = client.get("/api/cards/categories")
    assert resp.status_code == 200
    data = resp.json()
    cats = data["categories"]
    assert len(cats) >= 1
    for cat in cats:
        assert "name" in cat
        assert "count" in cat
        assert cat["count"] >= 1
    logger.info("  PASS: Categories (%d categories)", len(cats))


def test_stats() -> None:
    """Stats endpoint should return aggregate numbers."""
    client = _setup()
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cards"] >= _MIN_CARD_COUNT
    assert "total_downloads" in data
    assert "total_contributors" in data
    logger.info(
        "  PASS: Stats (cards: %d, contributors: %d)",
        data["total_cards"],
        data["total_contributors"],
    )


def main() -> None:
    """Run all API tests."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("\nTest: Cards API")
    logger.info("=" * 40)

    tests = [
        test_health,
        test_list_cards,
        test_get_single_card,
        test_get_card_not_found,
        test_search_cards,
        test_filter_by_category,
        test_sort_by_newest,
        test_download_card,
        test_rate_card,
        test_rate_card_update,
        test_rate_card_invalid,
        test_trending_cards,
        test_categories,
        test_stats,
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
