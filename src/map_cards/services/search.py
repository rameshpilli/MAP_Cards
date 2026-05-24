"""Full-text search and category queries for cards."""

from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from map_cards.models import Card

__all__ = ["search_cards", "get_categories_with_counts"]

# Valid sort-field names mapped to SQLAlchemy column orderings.
_SORT_FIELDS = {
    "downloads": Card.download_count.desc(),
    "rating": Card.avg_rating.desc(),
    "newest": Card.created_at.desc(),
    "trending": Card.trending_score.desc(),
}

_DEFAULT_SORT = "downloads"


def search_cards(
    db: Session,
    query: str,
    category: str | None = None,
    platform: str | None = None,
    sort_by: str = _DEFAULT_SORT,
    limit: int = 50,
    offset: int = 0,
) -> list[Card]:
    """Search cards by query across title, description, name, and author.

    Args:
        db: Database session.
        query: Search term (empty string returns all cards).
        category: Optional category filter.
        platform: Optional platform filter.
        sort_by: One of ``downloads``, ``rating``, ``newest``, ``trending``.
        limit: Maximum results to return.
        offset: Pagination offset.

    Returns:
        List of matching :class:`Card` objects.
    """
    q = db.query(Card)

    if query:
        search_term = f"%{query.lower()}%"
        q = q.filter(
            or_(
                Card.title.ilike(search_term),
                Card.description.ilike(search_term),
                Card.author.ilike(search_term),
                Card.name.ilike(search_term),
            ),
        )

    if category:
        q = q.filter(Card.category == category)

    if platform:
        q = q.filter(Card.platforms.contains(platform))

    order = _SORT_FIELDS.get(sort_by, _SORT_FIELDS[_DEFAULT_SORT])
    q = q.order_by(order)

    return q.offset(offset).limit(limit).all()


def get_categories_with_counts(db: Session) -> list[dict[str, str | int]]:
    """Return all categories with the number of cards in each."""
    results = (
        db.query(Card.category, func.count(Card.id).label("count"))
        .group_by(Card.category)
        .order_by(func.count(Card.id).desc())
        .all()
    )
    return [{"name": cat, "count": count} for cat, count in results]
