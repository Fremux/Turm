"""Add enabled_tools field to agent_configurations table."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.services.database import database_service
from app.core.logging import logger


def migrate():
    """Add enabled_tools column to agent_configurations table."""
    try:
        with database_service.engine.begin() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'agent_configurations'
                AND column_name = 'enabled_tools'
            """))
            existing_columns = {row[0] for row in result}

            if 'enabled_tools' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE agent_configurations
                    ADD COLUMN enabled_tools JSON DEFAULT '[]'::json
                """))
                logger.info("Added 'enabled_tools' column to agent_configurations table.")
            else:
                logger.info("'enabled_tools' column already exists.")

        logger.info("Enabled tools migration completed successfully.")
    except Exception as e:
        logger.error("enabled_tools_migration_failed", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("ENABLED TOOLS MIGRATION")
    logger.info("==================================================")
    migrate()
    logger.info("Migration script finished.")




