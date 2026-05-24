# MAPrompt Cards

## Project overview
MAPrompt Cards is a public marketplace for reusable AI prompt templates. Users can browse, search, install, and contribute prompt "cards" that work across Claude, Codex, GPT, and other AI platforms.

## Architecture
- **Backend**: FastAPI + SQLAlchemy + SQLite (dev) / Postgres (prod) in `src/map_cards/`
- **Frontend**: Single-page HTML dashboard (`web/index.html`)
- **Cards**: YAML files in `cards/` directory, synced to DB via `map_cards.services.card_sync`
- **CLI**: Node.js CLI (`npx map-cards install <name>`) in `cli/`

## Key commands
```bash
# Install dependencies
pip install -e ".[dev]"

# Seed database from YAML cards
python -m map_cards.seed

# Run API server
uvicorn map_cards.app:app --reload

# Run tests
python -m tests.test_card_validation
python -m tests.test_trending
python -m tests.test_search
python -m tests.test_cards_api

# Lint
ruff check src/ tests/

# Docker
docker-compose up --build
```

## Project structure
- `cards/` -- Card YAML files (the content)
- `schemas/` -- JSON Schema for card validation
- `src/map_cards/` -- Python package: app factory, config, models, API routes, services
- `web/` -- Single-page dashboard and static JSON
- `cli/` -- npm CLI tool
- `tests/` -- Test suite
- `scripts/` -- Build helpers (e.g. build_static.py)
- `docs/` -- Documentation

## Code conventions
- Python 3.11+, type hints everywhere, `from __future__ import annotations`
- FastAPI for API routes, SQLAlchemy 2.0 declarative base
- YAML for card definitions, validated against `schemas/card-schema.json`
- Tests use simple assert-based functions (no pytest dependency)
- Logging via `logging` module, no `print()` in library code
