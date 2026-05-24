"""Trending score computation for cards based on downloads, recency, and rating."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from map_cards.models import Card, Download

__all__ = ["compute_trending_score", "update_trending_scores"]

_SECONDS_PER_DAY = 86_400
_TRENDING_WINDOW_DAYS = 7
_MIN_RATING_BOOST = 0.1
_MAX_RATING = 5.0


def compute_trending_score(
    downloads_7d: int,
    days_since_update: float,
    avg_rating: float,
) -> float:
    """Compute a trending score for a single card.

    Formula::

        score = downloads_7d * recency * rating_boost

    Where *recency* decays with age and *rating_boost* is normalized to 0-1
    (minimum ``0.1`` so unrated cards still rank).
    """
    recency = 1.0 / (days_since_update + 1)
    rating_boost = max(avg_rating / _MAX_RATING, _MIN_RATING_BOOST)
    return downloads_7d * recency * rating_boost


def update_trending_scores(db: Session) -> int:
    """Recompute trending scores for every card.  Returns the count of updated cards."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=_TRENDING_WINDOW_DAYS)

    cards: list[Card] = db.query(Card).all()
    updated = 0

    for card in cards:
        downloads_7d: int = (
            db.query(func.count(Download.id))
            .filter(
                Download.card_name == card.name,
                Download.downloaded_at >= window_start,
            )
            .scalar()
            or 0
        )

        updated_at = card.updated_at or card.created_at or now
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        days_since_update = (now - updated_at).total_seconds() / _SECONDS_PER_DAY

        card.trending_score = compute_trending_score(
            downloads_7d=downloads_7d,
            days_since_update=days_since_update,
            avg_rating=card.avg_rating or 0.0,
        )
        updated += 1

    db.commit()
    return updated
