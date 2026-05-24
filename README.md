# MAPrompt Cards

[![CI](https://github.com/map-cards/map-cards/actions/workflows/ci.yml/badge.svg)](https://github.com/map-cards/map-cards/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

A public marketplace for reusable AI prompt templates.
Browse, install, and contribute prompt cards for Claude, Codex, GPT, and more.

## Quick start

```bash
pip install -e ".[dev]"
python -m map_cards.seed          # load cards from cards/ directory
uvicorn map_cards.app:app --reload  # start API on :8000
open http://localhost:8000
```

## Install a card

```bash
npx map-cards install full-stack-code-review
```

Or use the dashboard -- click **Install** to copy a prompt to your clipboard.

## Architecture

```
MAP_CARDS/
 ├── cards/               Card YAML registry (one dir per card)
 ├── src/map_cards/       Python package (FastAPI + SQLAlchemy)
 │    ├── app.py          Application factory
 │    ├── config.py       Settings via pydantic-settings
 │    ├── database.py     Engine, session, Base
 │    ├── models.py       ORM models (Card, Download, Rating)
 │    ├── seed.py         DB seeder
 │    ├── api/            Route modules
 │    └── services/       Business logic (sync, search, trending)
 ├── web/                 Single-page dashboard + static JSON
 ├── cli/                 Node.js CLI (npx map-cards)
 ├── schemas/             JSON Schema for card validation
 ├── scripts/             Build helpers
 ├── tests/               Test suite
 └── docs/                Documentation
```

## Available cards

| Card | Category | Description |
|------|----------|-------------|
| `full-stack-code-review` | code-review | Orchestrates 3 agents to review frontend, backend, and infra |
| `adversarial-prompt-fuzzer` | security | Adversarial test cases for AI guardrails |
| `adversarial-security-tester` | security | OWASP Top 10 assessment for web apps |
| `literature-review-pipeline` | research | Multi-stage literature review with gap analysis |
| `research-paper-summarizer` | research | Three-level paper analysis |
| `multi-db-migration-planner` | devops | Migration planning with rollback strategies |
| `pr-description-generator` | code-review | Structured PR descriptions from git diffs |
| `data-pipeline-debugger` | data | ETL pipeline failure diagnosis |
| `technical-blog-writer` | writing | Technical concepts to polished blog posts |

## Docker

```bash
docker-compose up --build
# API at http://localhost:8000
```

## API

See [docs/api.md](docs/api.md) for the full endpoint reference.

```bash
curl http://localhost:8000/api/cards           # list
curl http://localhost:8000/api/cards?q=security # search
curl -X POST http://localhost:8000/api/cards/full-stack-code-review/download
```

## Tests

```bash
python -m tests.test_card_validation
python -m tests.test_trending
python -m tests.test_search
python -m tests.test_cards_api
```

## Contribute

See [docs/contributing.md](docs/contributing.md) for how to add a new card.

## License

MIT
