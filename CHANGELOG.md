# Changelog

## 0.1.0 — 2026-05-24

### Added
- Initial release of MAPrompt Cards marketplace
- 9 curated prompt cards across code-review, security, research, devops, data, writing categories
- FastAPI backend with SQLite storage
- Card sync service (YAML files to database)
- Full-text search across card titles, descriptions, and tags
- Trending algorithm based on downloads, recency, and rating
- Download tracking and star ratings (1-5)
- Single-page HTML dashboard with category filters, search, and sort
- CLI tool (`npx map-cards install <name>`)
- JSON Schema validation for card YAML files
- GitHub Actions workflows for CI, card validation, and sync
- Docker and docker-compose support
- Comprehensive documentation and contribution guide
