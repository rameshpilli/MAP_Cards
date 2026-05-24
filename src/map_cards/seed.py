"""Seed the database from the cards/ directory."""

from __future__ import annotations

import logging

from map_cards.database import SessionLocal, create_tables
from map_cards.services.card_sync import sync_cards_from_directory
from map_cards.services.trending import update_trending_scores

logger = logging.getLogger(__name__)

_BANNER_WIDTH = 40


def main() -> None:
    """Load every card YAML into the database and recompute trending scores."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    logger.info("MAPrompt Cards -- Database Seeder")
    logger.info("=" * _BANNER_WIDTH)

    logger.info("Creating database tables...")
    create_tables()

    logger.info("Syncing cards from cards/ directory...")
    db = SessionLocal()
    try:
        results = sync_cards_from_directory(db)
        logger.info("  Synced: %d", results["synced"])
        logger.info("  Skipped: %d", results["skipped"])
        if results["errors"]:
            logger.warning("  Errors: %d", len(results["errors"]))
            for err in results["errors"]:
                logger.warning("    - %s", err)

        logger.info("Computing trending scores...")
        updated = update_trending_scores(db)
        logger.info("  Updated %d cards", updated)

        logger.info("=" * _BANNER_WIDTH)
        logger.info("Seed complete!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
