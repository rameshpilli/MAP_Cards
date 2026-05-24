"""Marketplace statistics and health-check endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from map_cards.database import get_db
from map_cards.models import Card

__all__ = ["router"]

router = APIRouter(tags=["analytics"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return aggregate marketplace statistics."""
    total_cards = db.query(func.count(Card.id)).scalar() or 0
    total_downloads = db.query(func.sum(Card.download_count)).scalar() or 0
    total_contributors = db.query(func.count(func.distinct(Card.author))).scalar() or 0
    avg_rating = (
        db.query(func.avg(Card.avg_rating)).filter(Card.rating_count > 0).scalar()
    )

    return {
        "total_cards": total_cards,
        "total_downloads": int(total_downloads),
        "total_contributors": total_contributors,
        "average_rating": round(float(avg_rating or 0), 1),
    }


@router.get("/health")
def health_check() -> dict[str, str]:
    """Liveness probe for load balancers and orchestrators."""
    return {"status": "healthy", "service": "map-cards"}
