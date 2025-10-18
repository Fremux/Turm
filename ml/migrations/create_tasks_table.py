"""Create tasks table for task management."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlmodel import SQLModel
from app.services.database import database_service
from app.models.task import Task
from app.core.logging import logger


def create_tables():
    """Create tasks table."""
    try:
        logger.info("Creating tasks table...")
        
        # Create tables using SQLModel
        SQLModel.metadata.create_all(
            database_service.engine,
            tables=[Task.__table__]
        )
        
        logger.info("Tasks table created successfully")
        
    except Exception as e:
        logger.error("failed_to_create_tasks_table", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    print("TASKS TABLE MIGRATION")
    print("=" * 50)
    create_tables()
    print("Migration completed successfully!")

