"""Tests for the Cards API endpoints."""

import sys

from fastapi.testclient import TestClient

from server.db.base import create_tables, engine, Base
from server.main import app
from server.services.card_sync import sync_cards_from_directory
from server.db.base import SessionLocal


def setup():
    """Set up test database with seeded cards."""
    Base.metadata.drop_all(bind=engine)
    create_tables()
    db = SessionLocal()
    try:
        sync_cards_from_directory(db)
    finally:
        db.close()
    return TestClient(app)


def test_health():
    """Health endpoint should return healthy."""
    client = setup()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    print("  PASS: Health check")


def test_list_cards():
    """List cards should return all seeded cards."""
    client = setup()
    resp = client.get("/api/cards")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 9, f"Expected >= 9 cards, got {data['count']}"
    assert len(data["cards"]) >= 9
    print(f"  PASS: List cards ({data['count']} cards)")


def test_get_single_card():
    """Get a specific card by name."""
    client = setup()
    resp = client.get("/api/cards/full-stack-code-review")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "full-stack-code-review"
    assert data["title"] == "Full-Stack Code Review Agent"
    assert len(data["prompt"]) > 100
    print("  PASS: Get single card")


def test_get_card_not_found():
    """Getting a non-existent card should return 404."""
    client = setup()
    resp = client.get("/api/cards/nonexistent-card")
    assert resp.status_code == 404
    print("  PASS: Card not found returns 404")


def test_search_cards():
    """Search should filter cards by query."""
    client = setup()
    resp = client.get("/api/cards?q=security")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1, "Expected at least 1 security-related card"
    for card in data["cards"]:
        text = (card["title"] + card["description"] + card["name"]).lower()
        assert "security" in text or "adversarial" in text, f"Card {card['name']} doesn't match 'security'"
    print(f"  PASS: Search cards ({data['count']} results for 'security')")


def test_filter_by_category():
    """Category filter should work."""
    client = setup()
    resp = client.get("/api/cards?category=research")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    for card in data["cards"]:
        assert card["category"] == "research"
    print(f"  PASS: Filter by category ({data['count']} research cards)")


def test_sort_by_newest():
    """Sort by newest should work."""
    client = setup()
    resp = client.get("/api/cards?sort=newest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 2
    # Check ordering
    dates = [c["created_at"] for c in data["cards"]]
    assert dates == sorted(dates, reverse=True), "Cards not sorted by newest"
    print("  PASS: Sort by newest")


def test_download_card():
    """Downloading a card should increment count and return prompt."""
    client = setup()
    resp = client.post("/api/cards/full-stack-code-review/download")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "full-stack-code-review"
    assert len(data["prompt"]) > 100
    assert data["download_count"] >= 1
    print(f"  PASS: Download card (count: {data['download_count']})")


def test_rate_card():
    """Rating a card should update its average."""
    client = setup()
    resp = client.post(
        "/api/cards/full-stack-code-review/rate",
        json={"user_id": "test-user-1", "stars": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["your_rating"] == 5
    assert data["avg_rating"] > 0
    assert data["rating_count"] >= 1
    print(f"  PASS: Rate card (avg: {data['avg_rating']}, count: {data['rating_count']})")


def test_rate_card_update():
    """Re-rating should update existing rating."""
    client = setup()
    # First rating
    client.post(
        "/api/cards/full-stack-code-review/rate",
        json={"user_id": "test-user-update", "stars": 2},
    )
    # Update rating
    resp = client.post(
        "/api/cards/full-stack-code-review/rate",
        json={"user_id": "test-user-update", "stars": 4},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["your_rating"] == 4
    print("  PASS: Update existing rating")


def test_rate_card_invalid():
    """Rating with invalid stars should fail."""
    client = setup()
    resp = client.post(
        "/api/cards/full-stack-code-review/rate",
        json={"user_id": "test-user-invalid", "stars": 6},
    )
    assert resp.status_code == 422
    print("  PASS: Invalid rating rejected")


def test_trending_cards():
    """Trending endpoint should return cards."""
    client = setup()
    resp = client.get("/api/cards/trending?limit=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["cards"]) <= 3
    print(f"  PASS: Trending cards ({len(data['cards'])} returned)")


def test_categories():
    """Categories endpoint should return categories with counts."""
    client = setup()
    resp = client.get("/api/cards/categories")
    assert resp.status_code == 200
    data = resp.json()
    cats = data["categories"]
    assert len(cats) >= 1
    for cat in cats:
        assert "name" in cat
        assert "count" in cat
        assert cat["count"] >= 1
    print(f"  PASS: Categories ({len(cats)} categories)")


def test_stats():
    """Stats endpoint should return aggregate numbers."""
    client = setup()
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cards"] >= 9
    assert "total_downloads" in data
    assert "total_contributors" in data
    print(f"  PASS: Stats (cards: {data['total_cards']}, contributors: {data['total_contributors']})")


def main():
    print("\nTest: Cards API")
    print("=" * 40)
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
