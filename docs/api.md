# MAPrompt Cards API Documentation

Base URL: `http://localhost:8000/api`

## Endpoints

### GET /api/cards
List all cards with optional search, filter, and sort.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | `""` | Search query (searches title, description, name, author) |
| `category` | string | — | Filter by category |
| `platform` | string | — | Filter by platform |
| `sort` | string | `"downloads"` | Sort by: `downloads`, `rating`, `newest`, `trending` |
| `limit` | int | `50` | Max results (1-100) |
| `offset` | int | `0` | Pagination offset |

**Response:**
```json
{
  "cards": [
    {
      "id": 1,
      "name": "full-stack-code-review",
      "title": "Full-Stack Code Review Agent",
      "description": "...",
      "author": "sarah-dev",
      "author_url": "https://github.com/sarah-dev",
      "category": "code-review",
      "tags": ["review", "multi-agent"],
      "platforms": ["claude", "codex", "gpt"],
      "prompt": "...",
      "variables": [...],
      "version": "1.0.0",
      "license": "MIT",
      "download_count": 42,
      "avg_rating": 4.5,
      "rating_count": 10,
      "trending_score": 3.75,
      "created_at": "2026-05-20T00:00:00+00:00",
      "updated_at": "2026-05-20T00:00:00+00:00"
    }
  ],
  "count": 1
}
```

### GET /api/cards/{name}
Get a single card by its slug name.

**Response:** Same card object as above.

**Errors:** `404` if card not found.

### POST /api/cards/{name}/download
Track a download and return the prompt text.

**Response:**
```json
{
  "name": "full-stack-code-review",
  "title": "Full-Stack Code Review Agent",
  "prompt": "...",
  "variables": [...],
  "download_count": 43
}
```

### POST /api/cards/{name}/rate
Rate a card 1-5 stars. Creates or updates the rating for the given user.

**Request Body:**
```json
{
  "user_id": "unique-user-id",
  "stars": 5
}
```

**Response:**
```json
{
  "name": "full-stack-code-review",
  "avg_rating": 4.5,
  "rating_count": 11,
  "your_rating": 5
}
```

**Errors:** `422` if stars is not 1-5 or user_id is empty.

### GET /api/cards/trending
Get the top trending cards.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | `10` | Max results (1-20) |

**Response:** Same format as list endpoint.

### GET /api/cards/categories
List all categories with their card counts.

**Response:**
```json
{
  "categories": [
    { "name": "code-review", "count": 2 },
    { "name": "security", "count": 2 },
    { "name": "research", "count": 2 }
  ]
}
```

### GET /api/stats
Get overall marketplace statistics.

**Response:**
```json
{
  "total_cards": 9,
  "total_downloads": 156,
  "total_contributors": 7,
  "average_rating": 4.2
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "map-cards"
}
```

## Error Responses
All errors follow the format:
```json
{
  "detail": "Error message"
}
```

Standard HTTP status codes:
- `200` — Success
- `404` — Resource not found
- `422` — Validation error
- `500` — Server error
