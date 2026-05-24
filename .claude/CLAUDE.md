# MAPrompt Cards — Multi-Agent Prompt Cards

## Project overview
MAPrompt Cards is a public marketplace for reusable AI prompt templates. Users can browse, search, install, and contribute prompt "cards" that work across Claude, Codex, GPT, and other AI platforms.

## Architecture
- **Backend**: FastAPI + SQLAlchemy + SQLite (dev) / Postgres (prod)
- **Frontend**: Single-page HTML dashboard (`client/index.html`)
- **Cards**: YAML files in `cards/` directory, synced to DB via `server/services/card_sync.py`
- **CLI**: Node.js CLI (`npx map-cards install <name>`)

## Key commands
```bash
# Install dependencies
pip install -e ".[dev]"

# Seed database from YAML cards
python -m server.seed

# Run API server
uvicorn server.main:app --reload

# Run tests
python -m tests.test_cards_api
python -m tests.test_trending
python -m tests.test_search
python -m tests.test_card_validation

# Docker
docker-compose up --build
```

## Project structure
- `cards/` — Card YAML files (the content)
- `schemas/` — JSON Schema for card validation
- `server/` — FastAPI backend (api/, db/, services/)
- `client/` — Single-page dashboard
- `cli/` — npm CLI tool
- `tests/` — Test suite
- `docs/` — Documentation

## Code conventions
- Python 3.13+, type hints everywhere
- FastAPI for API routes
- SQLAlchemy 2.0 style (mapped_column)
- YAML for card definitions
- Tests use simple assert-based functions (no pytest)
