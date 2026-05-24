"""Tests for full-text search across cards."""

import sys
from datetime import datetime, timezone

from server.db.base import SessionLocal, create_tables, engine, Base
from server.db.models import Card
from server.services.search import search_cards, get_categories_with_counts


def setup_db():
    """Create a fresh test database with sample cards."""
    Base.metadata.drop_all(bind=engine)
    create_tables()
    db = SessionLocal()

    now = datetime.now(timezone.utc)
    cards = [
        Card(
            name="test-react-review", title="React Code Review",
            description="Reviews React components for best practices",
            author="alice", category="code-review",
            tags=["react", "frontend"], platforms=["claude"],
            prompt="x" * 100, version="1.0.0",
            download_count=50, avg_rating=4.5, created_at=now, updated_at=now,
        ),
        Card(
            name="test-python-security", title="Python Security Scanner",
            description="Scans Python code for security vulnerabilities",
            author="bob", category="security",
            tags=["python", "security"], platforms=["claude", "gpt"],
            prompt="x" * 100, version="1.0.0",
            download_count=30, avg_rating=3.8, created_at=now, updated_at=now,
        ),
        Card(
            name="test-blog-writer", title="Technical Blog Writer",
            description="Writes technical blog posts from outlines",
            author="carol", category="writing",
            tags=["writing", "blog"], platforms=["gpt"],
            prompt="x" * 100, version="1.0.0",
            download_count=100, avg_rating=4.9, created_at=now, updated_at=now,
        ),
    ]
    db.add_all(cards)
    db.commit()
    return db


def test_search_by_title():
    """Search should match card titles."""
    db = setup_db()
    try:
        results = search_cards(db, query="React")
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        assert results[0].name == "test-react-review"
        print("  PASS: Search by title")
    finally:
        db.close()


def test_search_by_description():
    """Search should match card descriptions."""
    db = setup_db()
    try:
        results = search_cards(db, query="vulnerabilities")
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        assert results[0].name == "test-python-security"
        print("  PASS: Search by description")
    finally:
        db.close()


def test_search_by_author():
    """Search should match card authors."""
    db = setup_db()
    try:
        results = search_cards(db, query="carol")
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        assert results[0].name == "test-blog-writer"
        print("  PASS: Search by author")
    finally:
        db.close()


def test_search_empty_returns_all():
    """Empty search should return all cards."""
    db = setup_db()
    try:
        results = search_cards(db, query="")
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        print("  PASS: Empty search returns all")
    finally:
        db.close()


def test_filter_by_category():
    """Category filter should work."""
    db = setup_db()
    try:
        results = search_cards(db, query="", category="security")
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        assert results[0].category == "security"
        print("  PASS: Filter by category")
    finally:
        db.close()


def test_sort_by_downloads():
    """Sort by downloads should order correctly."""
    db = setup_db()
    try:
        results = search_cards(db, query="", sort_by="downloads")
        assert len(results) == 3
        assert results[0].download_count >= results[1].download_count
        assert results[1].download_count >= results[2].download_count
        print("  PASS: Sort by downloads")
    finally:
        db.close()


def test_sort_by_rating():
    """Sort by rating should order correctly."""
    db = setup_db()
    try:
        results = search_cards(db, query="", sort_by="rating")
        assert len(results) == 3
        assert results[0].avg_rating >= results[1].avg_rating
        assert results[1].avg_rating >= results[2].avg_rating
        print("  PASS: Sort by rating")
    finally:
        db.close()


def test_categories_with_counts():
    """Get categories should return correct counts."""
    db = setup_db()
    try:
        cats = get_categories_with_counts(db)
        assert len(cats) == 3, f"Expected 3 categories, got {len(cats)}"
        cat_dict = {c["name"]: c["count"] for c in cats}
        assert cat_dict["code-review"] == 1
        assert cat_dict["security"] == 1
        assert cat_dict["writing"] == 1
        print("  PASS: Categories with counts")
    finally:
        db.close()


def test_search_case_insensitive():
    """Search should be case-insensitive."""
    db = setup_db()
    try:
        results = search_cards(db, query="REACT")
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        print("  PASS: Case-insensitive search")
    finally:
        db.close()


def main():
    print("\nTest: Search")
    print("=" * 40)
    tests = [
        test_search_by_title,
        test_search_by_description,
        test_search_by_author,
        test_search_empty_returns_all,
        test_filter_by_category,
        test_sort_by_downloads,
        test_sort_by_rating,
        test_categories_with_counts,
        test_search_case_insensitive,
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
