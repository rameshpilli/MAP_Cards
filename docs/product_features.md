# MAPrompt Cards — Product Features

## What is MAPrompt Cards?

MAPrompt Cards (Multi-Agent Prompt Cards) is a public marketplace for reusable AI prompt templates. Think of it as npm for AI agent prompts — browse, install, and contribute prompt cards that work across Claude, Codex, GPT, and other AI platforms.

## Core Concepts

### Cards
A **card** is a structured prompt template stored as a YAML file. Each card includes:
- Metadata (name, author, category, tags, platforms)
- The prompt itself (real, useful, production-quality content)
- Variables (customizable parameters with defaults)

### Categories
Cards are organized into categories:
- **code-review** — Code analysis and review automation
- **security** — Security testing and vulnerability analysis
- **research** — Academic research and literature review
- **devops** — Infrastructure, deployment, and migration
- **data** — Data pipeline debugging and analytics
- **writing** — Technical writing and content generation
- **testing** — Test generation and QA automation
- **multi-agent** — Multi-agent orchestration patterns

### Platforms
Each card declares which AI platforms it's compatible with:
- Claude, Codex, GPT, Gemini, LLaMA, Mistral

## Features

### Browse & Search
- Full-text search across card titles, descriptions, tags, and authors
- Category filter pills for quick filtering
- Sort by: Most Installed, Highest Rated, Newest, Trending

### Install
- The dashboard "Install" action opens a target picker instead of silently copying text
- Codex bootstrap writes a `.codex/map-cards` artifact and an `AGENTS.md` reference
- Claude bootstrap writes a project `CLAUDE.md` memory entry plus a machine-readable manifest
- Markdown and raw prompt exports remain available for generic tools
- CLI: `npx map-cards install <card-name> --target codex --dir .`
- Download tracking for API-backed installs

### Rate
- Star ratings (1-5) per card
- One rating per user per card (can update)
- Average rating displayed on card

### Trending
The trending algorithm ranks cards by recent popularity:
```
score = downloads_7d * recency * rating_boost
```
Where:
- `downloads_7d` = download count in the last 7 days
- `recency = 1.0 / (days_since_update + 1)`
- `rating_boost = max(avg_rating / 5.0, 0.1)`

### Contribute
Anyone can contribute a card:
1. Fork the repo
2. Create `cards/your-card-name/card.yaml`
3. Open a PR
4. CI validates the YAML schema
5. On merge, the card auto-syncs to the database

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cards` | GET | List/search cards |
| `/api/cards/{name}` | GET | Get single card |
| `/api/cards/{name}/download` | POST | Download card |
| `/api/cards/{name}/rate` | POST | Rate card |
| `/api/cards/trending` | GET | Top trending |
| `/api/cards/categories` | GET | Categories with counts |
| `/api/stats` | GET | Marketplace stats |
| `/api/health` | GET | Health check |

## Architecture

- **Backend**: FastAPI + SQLAlchemy + SQLite (dev) / Postgres (prod)
- **Frontend**: Single-page HTML dashboard
- **Cards**: YAML files in `cards/` directory, synced to DB
- **CLI**: Node.js CLI (`npx map-cards`)

## Roadmap

### MVP (v0.1) - Current
- 9 curated prompt cards
- Browse, search, filter, sort
- Targeted install flow for Codex, Claude, Markdown, and raw prompt export
- Star ratings
- Trending algorithm
- Single-page dashboard
- CLI tool
- CI/CD validation

### V2 (v0.2)
- User accounts and authentication
- Card versioning and changelogs
- Card forking and remixing
- Comments and discussions
- Card collections (curated lists)
- Advanced search (filters, operators)
- API key for programmatic access

### V3 (v1.0)
- Card execution engine (run prompts directly)
- Variable interpolation UI
- Team workspaces
- Private cards
- Webhook integrations
- Usage analytics dashboard
- Plugin system for custom card types
