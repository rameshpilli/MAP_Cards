"""Download tracking endpoint."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from map_cards.database import get_db
from map_cards.models import Card, Download
from map_cards.services.bootstrap import (
    SUPPORTED_BOOTSTRAP_TARGETS,
    build_bootstrap_payload,
    build_install_options,
    normalize_bootstrap_target,
)

__all__ = ["router"]

router = APIRouter(prefix="/cards", tags=["downloads"])


@router.post("/{name}/download")
def download_card(
    name: str,
    request: Request,
    body: dict[str, Any] | None = Body(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Increment the download count for *name* and return install artifacts."""
    card = db.query(Card).filter(Card.name == name).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card '{name}' not found")

    body = body or {}
    target = normalize_bootstrap_target(str(body.get("target") or "prompt"))
    if target not in SUPPORTED_BOOTSTRAP_TARGETS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported bootstrap target '{target}'",
        )

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

    bootstrap = build_bootstrap_payload(card, target)
    return {
        "name": card.name,
        "title": card.title,
        "prompt": card.prompt,
        "variables": card.variables or [],
        "download_count": card.download_count,
        "install_options": build_install_options(card),
        "bootstrap": bootstrap,
    }


@router.get("/{name}/bootstrap", response_model=None)
def bootstrap_card(
    name: str,
    target: str = Query(
        "codex",
        description="Bootstrap target: codex, claude, markdown, json, yaml, prompt",
    ),
    download: bool = Query(False, description="When true, return the artifact as an attachment"),
    db: Session = Depends(get_db),
) -> dict[str, Any] | Response:
    """Return a target-specific bootstrap artifact without recording analytics."""
    card = db.query(Card).filter(Card.name == name).first()
    if not card:
        raise HTTPException(status_code=404, detail=f"Card '{name}' not found")

    target = normalize_bootstrap_target(target)
    if target not in SUPPORTED_BOOTSTRAP_TARGETS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported bootstrap target '{target}'",
        )

    payload = build_bootstrap_payload(card, target)
    if not download:
        return payload

    return Response(
        content=payload["content"],
        media_type=payload["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{payload["filename"]}"',
        },
    )
