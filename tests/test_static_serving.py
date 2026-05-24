"""Tests for serving the static frontend alongside the API."""

from __future__ import annotations

import json
from pathlib import Path

import map_cards.app as app_module
from fastapi.testclient import TestClient


def test_root_serves_frontend_index() -> None:
    """The app root should serve the bundled frontend HTML."""
    with TestClient(app_module.create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "MAP Cards" in response.text
    assert "/app.js" in response.text


def test_static_data_file_is_served() -> None:
    """Frontend data assets should be available from the mounted web directory."""
    expected_path = Path(__file__).resolve().parents[1] / "web" / "data" / "cards.json"
    expected_cards = json.loads(expected_path.read_text(encoding="utf-8"))

    with TestClient(app_module.create_app()) as client:
        response = client.get("/data/cards.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == expected_cards


def test_api_routes_remain_available_with_static_mount() -> None:
    """Static mounting at the root must not shadow API routes."""
    with TestClient(app_module.create_app()) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "map-cards"}


def test_root_falls_back_when_frontend_directory_is_missing(monkeypatch) -> None:
    """App creation should stay healthy when the frontend bundle is absent."""
    missing_dir = Path(__file__).resolve().parents[1] / "web-missing-for-test"
    monkeypatch.setattr(app_module, "_web_dir", lambda: missing_dir)

    with TestClient(app_module.create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "MAPrompt Cards API", "docs": "/docs"}
