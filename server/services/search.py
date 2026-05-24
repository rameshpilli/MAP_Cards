"""Full-text search across cards."""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from server.db.models import Card


def search_cards(
    db: Session,
    query: str,
    category: str | None = None,
    platform: str | None = None,
    sort_by: str = "downloads",
    limit: int = 50,
    offset: int = 0,
) -> list[Card]:
    """Search cards by query across title, description, tags, and author.

    Args:
        db: Database session
        query: Search query string (empty string returns all)
        category: Filter by category
        platform: Filter by platform
        sort_by: Sort field (downloads, rating, newest, trending)
        limit: Max results
        offset: Pagination offset

    Returns:
        List of matching Card objects
    """
    q = db.query(Card)

    # Apply search filter
    if query:
        search_term = f"%{query.lower()}%"
        q = q.filter(
            or_(
                Card.title.ilike(search_term),
                Card.description.ilike(search_term),
                Card.author.ilike(search_term),
                Card.name.ilike(search_term),
            )
        )

    # Apply category filter
    if category:
        q = q.filter(Card.category == category)

    # Apply platform filter (JSON array contains)
    if platform:
        # SQLite JSON handling
        q = q.filter(Card.platforms.contains(platform))

    # Apply sorting
    if sort_by == "downloads":
        q = q.order_by(Card.download_count.desc())
    elif sort_by == "rating":
        q = q.order_by(Card.avg_rating.desc())
    elif sort_by == "newest":
        q = q.order_by(Card.created_at.desc())
    elif sort_by == "trending":
        q = q.order_by(Card.trending_score.desc())
    else:
        q = q.order_by(Card.download_count.desc())

    return q.offset(offset).limit(limit).all()


def get_categories_with_counts(db: Session) -> list[dict]:
    """Get all categories with their card counts."""
    from sqlalchemy import func

    results = (
        db.query(Card.category, func.count(Card.id).label("count"))
        .group_by(Card.category)
        .order_by(func.count(Card.id).desc())
        .all()
    )
    return [{"name": cat, "count": count} for cat, count in results]
