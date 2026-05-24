# MAPrompt Cards — Multi-Agent Prompt Cards

A public marketplace for reusable AI prompt templates.
Browse, install, and contribute prompt cards for Claude, Codex, GPT, and more.

## Quick Start

```bash
# Run locally
pip install -e ".[dev]"
python -m server.seed    # Load cards from cards/ directory
uvicorn server.main:app  # Start API on :8000
open http://localhost:8000
```

## Install a Card

```bash
npx map-cards install full-stack-code-review
```

Or use the dashboard — click "Install" to copy a prompt to your clipboard.

## Available Cards

| Card | Category | Description |
|------|----------|-------------|
| `full-stack-code-review` | code-review | Orchestrates 3 agents to review frontend, backend, and infra changes |
| `adversarial-prompt-fuzzer` | security | Generates adversarial test cases for AI system guardrails |
| `adversarial-security-tester` | security | OWASP Top 10 security assessment for web applications |
| `literature-review-pipeline` | research | Multi-stage academic literature review with gap analysis |
| `research-paper-summarizer` | research | Three-level paper analysis: executive, detailed, and critical |
| `multi-db-migration-planner` | devops | Database migration planning with rollback and zero-downtime strategies |
| `pr-description-generator` | code-review | Generates structured PR descriptions from git diffs |
| `data-pipeline-debugger` | data | Diagnoses ETL pipeline failures with root cause analysis |
| `technical-blog-writer` | writing | Transforms technical concepts into polished blog posts |

## Docker

```bash
docker-compose up --build
# API available at http://localhost:8000
```

## API

See [API Documentation](docs/api.md) for the full endpoint reference.

```bash
# List all cards
curl http://localhost:8000/api/cards

# Search
curl http://localhost:8000/api/cards?q=security

# Get a specific card
curl http://localhost:8000/api/cards/full-stack-code-review

# Download (track + get prompt)
curl -X POST http://localhost:8000/api/cards/full-stack-code-review/download
```

## Contribute

See [Contributing Guide](docs/contributing.md) for how to add a new card.

## License

MIT
