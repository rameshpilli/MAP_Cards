"""Thin CLI entry point that delegates to the seed command.

Run via ``python -m map_cards.cli`` or the installed ``map-cards`` console script.
"""

from __future__ import annotations

from map_cards.seed import main

if __name__ == "__main__":
    main()
