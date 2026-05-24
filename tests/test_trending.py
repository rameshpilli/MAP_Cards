"""Tests for the trending score algorithm."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone

from map_cards.database import Base, SessionLocal, create_tables, engine
from map_cards.models import Card, Download
from map_cards.services.trending import compute_trending_score, update_trending_scores

logger = logging.getLogger(__name__)

_PROMPT_PLACEHOLDER = "x" * 100


def _setup_db() -> SessionLocal:
    """Create a fresh test database."""
    Base.metadata.drop_all(bind=engine)
    create_tables()
    return SessionLocal()


def test_compute_trending_basic() -> None:
    """Basic trending score computation."""
    score = compute_trending_score(
        downloads_7d=10,
        days_since_update=0,
        avg_rating=5.0,
    )
    # 10 * (1/1) * (5/5) = 10.0
    assert score == 10.0, f"Expected 10.0, got {score}"
    logger.info("  PASS: Basic trending score")


def test_compute_trending_recency_decay() -> None:
    """Score should decrease with older updates."""
    score_fresh = compute_trending_score(downloads_7d=10, days_since_update=0, avg_rating=5.0)
    score_old = compute_trending_score(downloads_7d=10, days_since_update=6, avg_rating=5.0)

    assert score_fresh > score_old, (
        f"Fresh score ({score_fresh}) should be > old score ({score_old})"
    )
    logger.info("  PASS: Recency decay works")


def test_compute_trending_rating_boost() -> None:
    """Higher rated cards should trend more."""
    score_high = compute_trending_score(downloads_7d=10, days_since_update=0, avg_rating=5.0)
    score_low = compute_trending_score(downloads_7d=10, days_since_update=0, avg_rating=1.0)

    assert score_high > score_low, (
        f"High-rated score ({score_high}) should be > low-rated ({score_low})"
    )
    logger.info("  PASS: Rating boost works")


def test_compute_trending_zero_rating() -> None:
    """Zero rating should still produce a score (minimum boost 0.1)."""
    score = compute_trending_score(downloads_7d=10, days_since_update=0, avg_rating=0.0)
    assert score > 0, f"Zero-rating score should be > 0, got {score}"
    logger.info("  PASS: Zero rating still scores (min boost)")


def test_compute_trending_no_downloads() -> None:
    """Zero downloads should produce zero score."""
    score = compute_trending_score(downloads_7d=0, days_since_update=0, avg_rating=5.0)
    assert score == 0.0, f"Zero downloads should give 0 score, got {score}"
    logger.info("  PASS: Zero downloads = zero score")


def test_update_trending_scores_integration() -> None:
    """Integration test: update_trending_scores with real DB records."""
    db = _setup_db()
    try:
        now = datetime.now(timezone.utc)

        card1 = Card(
            name="trending-test-1", title="Card 1", description="Test card one for trending",
            author="test", category="testing", tags=[], platforms=[], prompt=_PROMPT_PLACEHOLDER,
            version="1.0.0", avg_rating=4.5, created_at=now, updated_at=now,
        )
        card2 = Card(
            name="trending-test-2", title="Card 2", description="Test card two for trending",
            author="test", category="testing", tags=[], platforms=[], prompt=_PROMPT_PLACEHOLDER,
            version="1.0.0", avg_rating=2.0, created_at=now - timedelta(days=30),
            updated_at=now - timedelta(days=30),
        )
        db.add_all([card1, card2])
        db.flush()

        for i in range(5):
            db.add(Download(card_name="trending-test-1", downloaded_at=now - timedelta(hours=i)))

        for i in range(3):
            dl_time = now - timedelta(days=10 + i)
            db.add(Download(card_name="trending-test-2", downloaded_at=dl_time))

        db.commit()

        updated = update_trending_scores(db)
        assert updated == 2, f"Expected 2 updated, got {updated}"

        db.refresh(card1)
        db.refresh(card2)
        assert card1.trending_score > card2.trending_score, (
            f"card1 ({card1.trending_score}) should trend higher "
            f"than card2 ({card2.trending_score})"
        )
        logger.info("  PASS: Integration trending update")

    finally:
        db.close()


def main() -> None:
    """Run all trending tests."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("\nTest: Trending Algorithm")
    logger.info("=" * 40)

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
