"""Card listing, search, and detail endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from map_cards.database import get_db
from map_cards.models import Card
from map_cards.services.search import get_categories_with_counts, search_cards

__all__ = ["router"]

router = APIRouter(prefix="/cards", tags=["cards"])


def _card_to_dict(card: Card) -> dict[str, Any]:
    """Serialize a :class:`Card` ORM instance to a plain dictionary."""
    return {
        "id": card.id,
        "name": card.name,
        "title": card.title,
        "description": card.description,
        "author": card.author,
        "author_url": card.author_url,
        "category": card.category,
        "tags": card.tags or [],
        "platforms": card.platforms or [],
        "prompt": card.prompt,
        "variables": card.variables or [],
        "version": card.version,
        "license": card.license,
        "download_count": card.download_count,
        "avg_rating": round(card.avg_rating or 0.0, 1),
        "rating_count": card.rating_count or 0,
        "trending_score": round(card.trending_score or 0.0, 2),
        "created_at": card.created_at.isoformat() if card.created_at else None,
        "updated_at": card.updated_at.isoformat() if card.updated_at else None,
    }


@router.get("")
def list_cards(
    q: str = Query("", description="Search query"),
    category: str | None = Query(None, description="Filter by category"),
    platform: str | None = Query(None, description="Filter by platform"),
    sort: str = Query("downloads", description="Sort by: downloads, rating, newest, trending"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List all cards with optional search, filter, and sort."""
    cards = search_cards(
        db=db,
        query=q,
        category=category,
        platform=platform,
        sort_by=sort,
        limit=limit,
        offset=offset,
    )
    return {"cards": [_card_to_dict(c) for c in cards], "count": len(cards)}


@router.get("/trending")
def trending_cards(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return the top trending cards by trending score."""
    cards = (
        db.query(Card)
        .order_by(Card.trending_score.desc())
        .limit(limit)
        .all()
    )
    return {"cards": [_card_to_dict(c) for c in cards]}


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return all categories with their card counts."""
    return {"categories": get_categories_with_counts(db)}


@router.get("/{name}")
def get_card(name: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Retrieve a single card by its slug name."""
    card = db.query(Card).filter(Card.name == name).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card '{name}' not found")
    return _card_to_dict(card)
