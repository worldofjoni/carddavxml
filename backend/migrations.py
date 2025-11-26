"""
Database migration utilities
"""

import logging
from sqlalchemy import text
from database import engine

logger = logging.getLogger(__name__)


def migrate_database():
    """
    Apply database migrations to add new columns
    """
    logger.info("Checking for database migrations...")

    with engine.connect() as conn:
        try:
            # Check if settings table exists
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
            ))
            if not result.fetchone():
                logger.info("Settings table doesn't exist yet, will be created by SQLAlchemy")
                return

            # Check if last_sync column exists
            result = conn.execute(text("PRAGMA table_info(settings)"))
            columns = [row[1] for row in result.fetchall()]

            migrations_needed = []

            if 'last_sync' not in columns:
                migrations_needed.append("ALTER TABLE settings ADD COLUMN last_sync VARCHAR(50) DEFAULT ''")

            if 'last_sync_status' not in columns:
                migrations_needed.append("ALTER TABLE settings ADD COLUMN last_sync_status VARCHAR(20) DEFAULT ''")

            if 'last_sync_message' not in columns:
                migrations_needed.append("ALTER TABLE settings ADD COLUMN last_sync_message TEXT DEFAULT ''")

            if 'bidirectional_sync' not in columns:
                migrations_needed.append("ALTER TABLE settings ADD COLUMN bidirectional_sync BOOLEAN DEFAULT 0")

            if migrations_needed:
                logger.info(f"Applying {len(migrations_needed)} database migrations...")
                for migration in migrations_needed:
                    logger.info(f"Running: {migration}")
                    conn.execute(text(migration))
                    conn.commit()
                logger.info("Database migrations completed successfully")
            else:
                logger.info("Database schema is up to date")

        except Exception as e:
            logger.error(f"Error during database migration: {str(e)}")
            raise
