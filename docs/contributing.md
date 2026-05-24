# Contributing to MAPrompt Cards

Thank you for your interest in contributing to MAPrompt Cards! This guide explains how to add a new prompt card to the marketplace.

## How to Add a Card

### 1. Fork the Repository
Fork the MAPrompt Cards repo and clone it locally.

### 2. Create Your Card Directory
Create a new directory under `cards/` with your card's slug name:

```bash
mkdir cards/your-card-name
```

The directory name must:
- Be lowercase
- Use hyphens for word separation
- Match the `name` field in your YAML

### 3. Write Your Card YAML
Create `cards/your-card-name/card.yaml` following the [Card Format Reference](card_format.md).

```yaml
name: your-card-name
version: "1.0.0"
title: "Your Card Title"
description: "A clear description of what your card does (10-500 chars)"
author: "your-github-username"
author_url: "https://github.com/your-username"
category: "code-review"  # See categories below
tags: ["tag1", "tag2"]
platforms: ["claude", "codex", "gpt"]
created_at: "2026-05-24"
updated_at: "2026-05-24"
license: "MIT"
prompt: |
  Your actual prompt content goes here.
  This must be real, useful content — not placeholder text.
  Minimum 50 characters.
variables:
  - name: variable_name
    description: "What this variable controls"
    default: "default value"
```

### 4. Validate Your Card
Run the validation tests locally:

```bash
pip install -e ".[dev]"
python -m tests.test_card_validation
```

### 5. Open a Pull Request
Push your branch and open a PR. The CI will automatically:
- Validate your YAML against the JSON Schema
- Check that all required fields are present
- Verify the card can be synced to the database

### 6. Review & Merge
A maintainer will review your card for:
- Prompt quality (is it genuinely useful?)
- Correct categorization
- Proper formatting
- No harmful or misleading content

On merge, your card automatically appears on the dashboard.

## Categories

| Category | Description |
|----------|-------------|
| `code-review` | Code analysis and review automation |
| `security` | Security testing and vulnerability analysis |
| `research` | Academic research and literature review |
| `devops` | Infrastructure, deployment, and migration |
| `data` | Data pipeline debugging and analytics |
| `writing` | Technical writing and content generation |
| `testing` | Test generation and QA automation |
| `multi-agent` | Multi-agent orchestration patterns |

## Platforms

Your card can target one or more platforms:
- `claude` — Anthropic Claude
- `codex` — OpenAI Codex
- `gpt` — OpenAI GPT
- `gemini` — Google Gemini
- `llama` — Meta LLaMA
- `mistral` — Mistral AI

## Quality Guidelines

### Do
- Write prompts that solve a real problem
- Include clear structure (headers, sections, steps)
- Add variables for customizable parts
- Test your prompt on at least one platform
- Be specific about expected inputs and outputs

### Don't
- Submit placeholder or lorem ipsum text
- Copy prompts from other sources without attribution
- Include harmful, offensive, or misleading content
- Submit prompts that require paid API access to validate
- Use overly generic titles ("My Prompt", "Test Card")

## Updating an Existing Card
To update a card you authored:
1. Bump the `version` field
2. Update the `updated_at` date
3. Open a PR with the changes

## Getting Help
- Open an issue on GitHub for questions
- Check existing cards for examples of good formatting
