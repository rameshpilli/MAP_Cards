"""Download tracking API endpoints."""

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from server.db.base import get_db
from server.db.models import Card, Download

router = APIRouter(prefix="/cards", tags=["downloads"])


@router.post("/{name}/download")
def download_card(name: str, request: Request, db: Session = Depends(get_db)):
    """Increment download count and return the prompt text."""
    card = db.query(Card).filter(Card.name == name).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card '{name}' not found")

    # Hash the client IP for anonymized tracking
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    # Record download
    download = Download(
        card_name=name,
        downloaded_at=datetime.now(timezone.utc),
        ip_hash=ip_hash,
    )
    db.add(download)

    # Increment card download count
    card.download_count = (card.download_count or 0) + 1
    db.commit()

    return {
        "name": card.name,
        "title": card.title,
        "prompt": card.prompt,
        "variables": card.variables or [],
        "download_count": card.download_count,
    }
