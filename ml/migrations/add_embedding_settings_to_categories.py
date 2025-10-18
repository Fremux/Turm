"""Add embedding settings to categories table."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.services.database import database_service
from app.core.logging import logger


def migrate():
    """Add embedding_model and embedding_dimension columns to categories table."""
    try:
        with database_service.engine.begin() as conn:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'categories' 
                AND column_name IN ('embedding_model', 'embedding_dimension')
            """))
            existing_columns = {row[0] for row in result}
            
            # Add embedding_model column if it doesn't exist
            if 'embedding_model' not in existing_columns:
                logger.info("adding_embedding_model_column")
                conn.execute(text("""
                    ALTER TABLE categories 
                    ADD COLUMN embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small'
                """))
                logger.info("embedding_model_column_added")
            else:
                logger.info("embedding_model_column_already_exists")
            
            # Add embedding_dimension column if it doesn't exist
            if 'embedding_dimension' not in existing_columns:
                logger.info("adding_embedding_dimension_column")
                conn.execute(text("""
                    ALTER TABLE categories 
                    ADD COLUMN embedding_dimension INTEGER DEFAULT 1536
                """))
                logger.info("embedding_dimension_column_added")
            else:
                logger.info("embedding_dimension_column_already_exists")
            
            logger.info("migration_completed_successfully")
            
    except Exception as e:
        logger.error("migration_failed", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    migrate()

