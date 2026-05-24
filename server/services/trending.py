"""Trending algorithm for MAPrompt Cards."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from server.db.models import Card, Download


def compute_trending_score(
    downloads_7d: int,
    days_since_update: float,
    avg_rating: float,
) -> float:
    """Compute trending score for a card.

    Formula: downloads_7d * recency * rating_boost
    - recency = 1.0 / (days_since_update + 1)
    - rating_boost = avg_rating / 5.0 (minimum 0.1 to avoid zeroing out)
    """
    recency = 1.0 / (days_since_update + 1)
    rating_boost = max(avg_rating / 5.0, 0.1)
    return downloads_7d * recency * rating_boost


def update_trending_scores(db: Session) -> int:
    """Recompute trending scores for all cards. Returns count of updated cards."""
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    cards = db.query(Card).all()
    updated = 0

    for card in cards:
        # Count downloads in last 7 days
        downloads_7d = (
            db.query(func.count(Download.id))
            .filter(
                Download.card_name == card.name,
                Download.downloaded_at >= seven_days_ago,
            )
            .scalar()
            or 0
        )

        # Calculate days since last update
        updated_at = card.updated_at or card.created_at or now
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        days_since_update = (now - updated_at).total_seconds() / 86400

        # Compute and store score
        card.trending_score = compute_trending_score(
            downloads_7d=downloads_7d,
            days_since_update=days_since_update,
            avg_rating=card.avg_rating or 0.0,
        )
        updated += 1

    db.commit()
    return updated
