"""Seed the database from the cards/ directory."""

import sys

from server.db.base import SessionLocal, create_tables
from server.services.card_sync import sync_cards_from_directory
from server.services.trending import update_trending_scores


def main():
    """Seed the database with cards from the cards/ directory."""
    print("MAPrompt Cards — Database Seeder")
    print("=" * 40)

    # Create tables
    print("Creating database tables...")
    create_tables()

    # Sync cards from directory
    print("Syncing cards from cards/ directory...")
    db = SessionLocal()
    try:
        results = sync_cards_from_directory(db)
        print(f"  Synced: {results['synced']}")
        print(f"  Skipped: {results['skipped']}")
        if results["errors"]:
            print(f"  Errors: {len(results['errors'])}")
            for err in results["errors"]:
                print(f"    - {err}")

        # Update trending scores
        print("Computing trending scores...")
        updated = update_trending_scores(db)
        print(f"  Updated {updated} cards")

        print("=" * 40)
        print("Seed complete!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
