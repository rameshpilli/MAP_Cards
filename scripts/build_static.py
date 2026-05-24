#!/usr/bin/env python3
"""Build static cards.json from all cards/*/card.yaml files.

Usage:
    python scripts/build_static.py

Outputs:
    client/data/cards.json  — consumed by the static GitHub Pages site.
"""

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "cards"
OUT_DIR = ROOT / "client" / "data"

cards = []
for card_dir in sorted(CARDS_DIR.iterdir()):
    yaml_path = card_dir / "card.yaml"
    if not yaml_path.exists():
        continue
    data = yaml.safe_load(yaml_path.read_text())
    # Add mock download/rating data for initial launch
    data.setdefault("download_count", 0)
    data.setdefault("avg_rating", 4.5)
    data.setdefault("rating_count", 0)
    cards.append(data)

OUT_DIR.mkdir(parents=True, exist_ok=True)
out_path = OUT_DIR / "cards.json"
out_path.write_text(json.dumps(cards, indent=2))
print(f"Built {len(cards)} cards -> {out_path}")
