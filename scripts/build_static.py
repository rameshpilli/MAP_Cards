#!/usr/bin/env python3
"""Build a static ``cards.json`` from all ``cards/*/card.yaml`` files.

Usage::

    python scripts/build_static.py

Output::

    web/data/cards.json  -- consumed by the GitHub Pages dashboard.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "cards"
OUT_DIR = ROOT / "web" / "data"

_DEFAULT_AVG_RATING = 4.5


def main() -> None:
    """Read every card YAML and emit a single JSON array."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    cards: list[dict] = []
    for card_dir in sorted(CARDS_DIR.iterdir()):
        yaml_path = card_dir / "card.yaml"
        if not yaml_path.exists():
            continue
        data = yaml.safe_load(yaml_path.read_text())
        data.setdefault("download_count", 0)
        data.setdefault("avg_rating", _DEFAULT_AVG_RATING)
        data.setdefault("rating_count", 0)
        cards.append(data)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "cards.json"
    out_path.write_text(json.dumps(cards, indent=2))
    logger.info("Built %d cards -> %s", len(cards), out_path)


if __name__ == "__main__":
    main()
