"""Tests for the trending algorithm."""

import sys
from datetime import datetime, timedelta, timezone

from server.db.base import SessionLocal, create_tables, engine, Base
from server.db.models import Card, Download
from server.services.trending import compute_trending_score, update_trending_scores


def setup_db():
    """Create a fresh test database."""
    Base.metadata.drop_all(bind=engine)
    create_tables()
    return SessionLocal()


def test_compute_trending_basic():
    """Basic trending score computation."""
    score = compute_trending_score(
        downloads_7d=10,
        days_since_update=0,
        avg_rating=5.0,
    )
    # 10 * (1/1) * (5/5) = 10.0
    assert score == 10.0, f"Expected 10.0, got {score}"
    print("  PASS: Basic trending score")


def test_compute_trending_recency_decay():
    """Score should decrease with older updates."""
    score_fresh = compute_trending_score(downloads_7d=10, days_since_update=0, avg_rating=5.0)
    score_old = compute_trending_score(downloads_7d=10, days_since_update=6, avg_rating=5.0)

    assert score_fresh > score_old, (
        f"Fresh score ({score_fresh}) should be > old score ({score_old})"
    )
    print("  PASS: Recency decay works")


def test_compute_trending_rating_boost():
    """Higher rated cards should trend more."""
    score_high = compute_trending_score(downloads_7d=10, days_since_update=0, avg_rating=5.0)
    score_low = compute_trending_score(downloads_7d=10, days_since_update=0, avg_rating=1.0)

    assert score_high > score_low, (
        f"High-rated score ({score_high}) should be > low-rated ({score_low})"
    )
    print("  PASS: Rating boost works")


def test_compute_trending_zero_rating():
    """Zero rating should still produce a score (minimum boost 0.1)."""
    score = compute_trending_score(downloads_7d=10, days_since_update=0, avg_rating=0.0)
    assert score > 0, f"Zero-rating score should be > 0, got {score}"
    print("  PASS: Zero rating still scores (min boost)")


def test_compute_trending_no_downloads():
    """Zero downloads should produce zero score."""
    score = compute_trending_score(downloads_7d=0, days_since_update=0, avg_rating=5.0)
    assert score == 0.0, f"Zero downloads should give 0 score, got {score}"
    print("  PASS: Zero downloads = zero score")


def test_update_trending_scores_integration():
    """Integration test: update_trending_scores with real DB records."""
    db = setup_db()
    try:
        now = datetime.now(timezone.utc)

        # Create two cards
        card1 = Card(
            name="trending-test-1", title="Card 1", description="Test card one for trending",
            author="test", category="testing", tags=[], platforms=[], prompt="x" * 100,
            version="1.0.0", avg_rating=4.5, created_at=now, updated_at=now,
        )
        card2 = Card(
            name="trending-test-2", title="Card 2", description="Test card two for trending",
            author="test", category="testing", tags=[], platforms=[], prompt="x" * 100,
            version="1.0.0", avg_rating=2.0, created_at=now - timedelta(days=30),
            updated_at=now - timedelta(days=30),
        )
        db.add_all([card1, card2])
        db.flush()

        # Add downloads for card1 (recent)
        for i in range(5):
            db.add(Download(card_name="trending-test-1", downloaded_at=now - timedelta(hours=i)))

        # Add downloads for card2 (old)
        for i in range(3):
            db.add(Download(card_name="trending-test-2", downloaded_at=now - timedelta(days=10 + i)))

        db.commit()

        # Update scores
        updated = update_trending_scores(db)
        assert updated == 2, f"Expected 2 updated, got {updated}"

        # card1 should have higher score (more recent downloads + higher rating + fresher update)
        db.refresh(card1)
        db.refresh(card2)
        assert card1.trending_score > card2.trending_score, (
            f"card1 ({card1.trending_score}) should trend higher than card2 ({card2.trending_score})"
        )
        print("  PASS: Integration trending update")

    finally:
        db.close()


def main():
    print("\nTest: Trending Algorithm")
    print("=" * 40)
    tests = [
        test_compute_trending_basic,
        test_compute_trending_recency_decay,
        test_compute_trending_rating_boost,
        test_compute_trending_zero_rating,
        test_compute_trending_no_downloads,
        test_update_trending_scores_integration,
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
