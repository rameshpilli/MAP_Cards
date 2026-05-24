"""Download tracking endpoint."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from map_cards.database import get_db
from map_cards.models import Card, Download

__all__ = ["router"]

router = APIRouter(prefix="/cards", tags=["downloads"])


@router.post("/{name}/download")
def download_card(
    name: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Increment the download count for *name* and return its prompt text."""
    card = db.query(Card).filter(Card.name == name).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card '{name}' not found")

    # Hash the client IP for anonymized tracking.
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    download = Download(
        card_name=name,
        downloaded_at=datetime.now(timezone.utc),
        ip_hash=ip_hash,
    )
    db.add(download)

    card.download_count = (card.download_count or 0) + 1
    db.commit()

    return {
        "name": card.name,
        "title": card.title,
        "prompt": card.prompt,
        "variables": card.variables or [],
        "download_count": card.download_count,
    }
