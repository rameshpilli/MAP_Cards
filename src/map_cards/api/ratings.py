"""Star-rating endpoint for cards."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from map_cards.database import get_db
from map_cards.models import Card, Rating

__all__ = ["router"]

router = APIRouter(prefix="/cards", tags=["ratings"])

_MIN_STARS = 1
_MAX_STARS = 5


class RatingRequest(BaseModel):
    """Payload for rating a card."""

    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    stars: int = Field(..., ge=_MIN_STARS, le=_MAX_STARS, description="Rating from 1 to 5 stars")


@router.post("/{name}/rate")
def rate_card(
    name: str,
    body: RatingRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Rate a card 1-5 stars.  Updates the existing rating if the user already rated."""
    card = db.query(Card).filter(Card.name == name).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card '{name}' not found")

    existing = (
        db.query(Rating)
        .filter(Rating.card_name == name, Rating.user_id == body.user_id)
        .first()
    )

    if existing:
        existing.stars = body.stars
        existing.created_at = datetime.now(timezone.utc)
    else:
        rating = Rating(
            card_name=name,
            user_id=body.user_id,
            stars=body.stars,
            created_at=datetime.now(timezone.utc),
        )
        db.add(rating)

    db.flush()

    # Recalculate aggregate rating.
    avg_result = (
        db.query(func.avg(Rating.stars), func.count(Rating.id))
        .filter(Rating.card_name == name)
        .first()
    )

    card.avg_rating = round(float(avg_result[0] or 0), 2)
    card.rating_count = int(avg_result[1] or 0)
    db.commit()

    return {
        "name": card.name,
        "avg_rating": card.avg_rating,
        "rating_count": card.rating_count,
        "your_rating": body.stars,
    }
