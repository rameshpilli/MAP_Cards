"""Install and bootstrap artifacts for prompt cards."""

from __future__ import annotations

import json
from typing import Any

import yaml

from map_cards.models import Card

__all__ = [
    "SUPPORTED_BOOTSTRAP_TARGETS",
    "build_bootstrap_payload",
    "build_install_options",
    "card_to_manifest",
    "normalize_bootstrap_target",
    "render_card_markdown",
]

SUPPORTED_BOOTSTRAP_TARGETS = {"codex", "claude", "markdown", "json", "yaml", "prompt"}


def normalize_bootstrap_target(target: str) -> str:
    """Normalize target aliases while preserving old cloud requests."""
    normalized = target.lower()
    return "claude" if normalized == "cloud" else normalized


def _variables_markdown(variables: list[dict[str, Any]]) -> str:
    if not variables:
        return "No variables declared."

    rows = []
    for variable in variables:
        default = variable.get("default") or ""
        rows.append(
            f"- `{variable.get('name', '')}`: {variable.get('description', '')}"
            + (f" Default: `{default}`." if default else ""),
        )
    return "\n".join(rows)


def card_to_manifest(card: Card) -> dict[str, Any]:
    """Return a portable manifest for a card."""
    return {
        "name": card.name,
        "title": card.title,
        "description": card.description,
        "author": card.author,
        "author_url": card.author_url,
        "category": card.category,
        "tags": card.tags or [],
        "platforms": card.platforms or [],
        "version": card.version,
        "license": card.license,
        "variables": card.variables or [],
        "prompt": card.prompt,
    }


def render_card_markdown(card: Card, *, codex: bool = False, claude: bool = False) -> str:
    """Render a card as a Markdown prompt artifact."""
    heading = f"# MAPrompt Card: {card.title}" if codex or claude else f"# {card.title}"
    usage_note = ""
    if codex:
        usage_note = (
            "\n## Codex Usage\n"
            "Use this card as task-specific operating guidance when the user asks for "
            f"{card.description.lower()}\n"
        )
    if claude:
        usage_note = (
            "\n## Claude Usage\n"
            "Use this card as project memory guidance in CLAUDE.md when the task asks for "
            f"{card.description.lower()}\n"
        )

    return (
        f"{heading}\n\n"
        f"Name: `{card.name}`\n"
        f"Version: `{card.version}`\n"
        f"Category: `{card.category}`\n"
        f"Platforms: {', '.join(card.platforms or [])}\n"
        f"License: {card.license}\n\n"
        f"## Description\n{card.description}\n"
        f"{usage_note}\n"
        f"## Variables\n{_variables_markdown(card.variables or [])}\n\n"
        f"## Prompt\n{card.prompt.rstrip()}\n"
    )


def _render_claude_manifest(card: Card) -> str:
    manifest = {
        "schema_version": "map-cards.claude.v1",
        "card": card_to_manifest(card),
        "claude": {
            "name": card.name,
            "display_name": card.title,
            "memory_file": "CLAUDE.md",
            "memory_entry": render_card_markdown(card, claude=True),
            "variables": card.variables or [],
        },
    }
    return json.dumps(manifest, indent=2)


def _render_yaml(card: Card) -> str:
    return yaml.safe_dump(card_to_manifest(card), sort_keys=False, allow_unicode=False)


def build_install_options(card: Card, api_base_url: str | None = None) -> list[dict[str, Any]]:
    """Return product-facing install options for a card."""
    base = (api_base_url or "/api").rstrip("/")
    encoded_name = card.name
    return [
        {
            "target": "codex",
            "label": "Bootstrap into Codex",
            "description": "Creates a .codex/map-cards prompt file and an AGENTS.md reference.",
            "command": f"npx map-cards install {card.name} --target codex --dir .",
            "endpoint": f"{base}/cards/{encoded_name}/bootstrap?target=codex",
            "filename": f"{card.name}.codex.md",
        },
        {
            "target": "claude",
            "label": "Install into Claude",
            "description": "Creates a CLAUDE.md memory entry that Claude Code can load.",
            "command": f"npx map-cards install {card.name} --target claude --dir .",
            "endpoint": f"{base}/cards/{encoded_name}/bootstrap?target=claude",
            "filename": f"{card.name}.claude.json",
        },
        {
            "target": "markdown",
            "label": "Download Markdown",
            "description": "Saves the card as a readable prompt file for any AI tool.",
            "command": f"npx map-cards install {card.name} --target markdown --dir .",
            "endpoint": f"{base}/cards/{encoded_name}/bootstrap?target=markdown",
            "filename": f"{card.name}.md",
        },
        {
            "target": "prompt",
            "label": "Copy prompt",
            "description": "Copies only the raw prompt text.",
            "command": "",
            "endpoint": f"{base}/cards/{encoded_name}/bootstrap?target=prompt",
            "filename": f"{card.name}.txt",
        },
    ]


def build_bootstrap_payload(
    card: Card,
    target: str,
    api_base_url: str | None = None,
) -> dict[str, Any]:
    """Build one bootstrap artifact response for *target*."""
    target = normalize_bootstrap_target(target)
    if target not in SUPPORTED_BOOTSTRAP_TARGETS:
        valid = ", ".join(sorted(SUPPORTED_BOOTSTRAP_TARGETS))
        raise ValueError(f"Unsupported bootstrap target '{target}'. Expected one of: {valid}")

    content_type = "text/plain"
    filename = f"{card.name}.txt"
    content = card.prompt
    next_steps = ["Paste the prompt into your AI tool."]

    if target == "codex":
        content_type = "text/markdown"
        filename = f"{card.name}.codex.md"
        content = render_card_markdown(card, codex=True)
        next_steps = [
            "Run the Codex install command from the workspace root.",
            (
                "Commit the generated .codex/map-cards artifact if the card should "
                "travel with the repo."
            ),
            "Codex will see the managed AGENTS.md reference on future sessions.",
        ]
    elif target == "claude":
        content_type = "application/json"
        filename = f"{card.name}.claude.json"
        content = _render_claude_manifest(card)
        next_steps = [
            "Run the Claude install command from the workspace root.",
            "The CLI appends a managed MAPrompt Cards section to CLAUDE.md.",
            "Start Claude Code from this workspace so it can load CLAUDE.md.",
        ]
    elif target == "markdown":
        content_type = "text/markdown"
        filename = f"{card.name}.md"
        content = render_card_markdown(card)
        next_steps = ["Add the Markdown file to your prompt library or project documentation."]
    elif target == "json":
        content_type = "application/json"
        filename = f"{card.name}.json"
        content = json.dumps(card_to_manifest(card), indent=2)
        next_steps = ["Import the JSON manifest into your prompt tooling."]
    elif target == "yaml":
        content_type = "application/yaml"
        filename = f"{card.name}.yaml"
        content = _render_yaml(card)
        next_steps = ["Place the YAML file under cards/<name>/card.yaml to contribute or remix it."]

    option = next(
        (item for item in build_install_options(card, api_base_url) if item["target"] == target),
        {},
    )
    return {
        "name": card.name,
        "title": card.title,
        "target": target,
        "label": option.get("label", target),
        "description": option.get("description", ""),
        "command": option.get("command", ""),
        "filename": filename,
        "content_type": content_type,
        "content": content,
        "next_steps": next_steps,
    }
