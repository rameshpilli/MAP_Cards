# Card YAML Format Reference

Every MAP Card is defined as a YAML file at `cards/<card-name>/card.yaml`. This document describes all available fields.

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | URL-safe slug identifier. Must match directory name. Pattern: `^[a-z0-9][a-z0-9-]*[a-z0-9]$` |
| `version` | string | Semantic version (e.g., `"1.0.0"`) |
| `title` | string | Human-readable title (3-100 chars) |
| `description` | string | Short description (10-500 chars) |
| `author` | string | Author handle or name |
| `category` | string | One of: `code-review`, `security`, `research`, `devops`, `data`, `writing`, `testing`, `multi-agent` |
| `tags` | array[string] | 1-10 searchable tags |
| `platforms` | array[string] | Compatible platforms: `claude`, `codex`, `gpt`, `gemini`, `llama`, `mistral` |
| `prompt` | string | The full prompt template (min 50 chars) |

## Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `author_url` | string (URI) | — | URL to author profile |
| `created_at` | string (date) | today | Date card was created (YYYY-MM-DD) |
| `updated_at` | string (date) | today | Date card was last updated |
| `license` | string | `"MIT"` | License for the prompt |
| `variables` | array[object] | `[]` | Template variables (see below) |

## Variables

Variables allow users to customize parts of the prompt. Each variable is an object with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable identifier |
| `description` | string | Yes | What the variable controls |
| `default` | string | No | Default value |

## Full Example

```yaml
name: example-card
version: "1.0.0"
title: "Example Card Title"
description: "A clear description of what this card does and when to use it."
author: "your-username"
author_url: "https://github.com/your-username"
category: "code-review"
tags: ["example", "template"]
platforms: ["claude", "codex", "gpt"]
created_at: "2026-05-24"
updated_at: "2026-05-24"
license: "MIT"
prompt: |
  You are a [role]. Your task is to [task description].

  ## Steps
  1. First, do [step 1]
  2. Then, [step 2]
  3. Finally, [step 3]

  ## Output Format
  - [Format specification]
  - [Expected structure]

  ## Rules
  - [Rule 1]
  - [Rule 2]
variables:
  - name: role
    description: "The role the AI should assume"
    default: "senior developer"
  - name: output_format
    description: "Preferred output format"
    default: "markdown"
```

## Validation

Cards are validated against the JSON Schema at `schemas/card-schema.json`. Run validation locally:

```bash
python -m tests.test_card_validation
```

The schema enforces:
- All required fields are present
- `name` matches the slug pattern
- `version` is valid semver
- `title` is 3-100 characters
- `description` is 10-500 characters
- `category` is one of the allowed values
- `platforms` contains only known platform names
- `tags` has 1-10 entries
- `prompt` is at least 50 characters
- No additional/unknown fields
