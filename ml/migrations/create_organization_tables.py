"""Create organization structure tables for role-based task assignment.

This migration creates:
- organization_units: stores the organizational hierarchy from users.json
- task_capability_mappings: maps tasks to roles that can handle them
- Updates tasks table with assigned_role_id field
"""

import asyncio
from sqlmodel import SQLModel, create_engine, Session, text

from app.core.config import settings
from app.core.logging import logger
from app.models.organization import OrganizationUnit, TaskCapabilityMapping
from app.models.task import Task


async def create_tables():
    """Create organization tables."""
    logger.info("Creating organization structure tables...")
    
    connection_url = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    engine = create_engine(connection_url, echo=False)
    
    # Create tables
    SQLModel.metadata.create_all(engine, tables=[
        OrganizationUnit.__table__,
        TaskCapabilityMapping.__table__
    ])
    
    # Add assigned_role_id to tasks table if it doesn't exist
    with Session(engine) as session:
        try:
            # Check if column exists
            result = session.exec(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='tasks' AND column_name='assigned_role_id'
            """)).first()
            
            if not result:
                logger.info("Adding assigned_role_id column to tasks table...")
                session.exec(text("""
                    ALTER TABLE tasks 
                    ADD COLUMN assigned_role_id INTEGER REFERENCES organization_units(id)
                """))
                session.exec(text("""
                    CREATE INDEX IF NOT EXISTS ix_tasks_assigned_role_id 
                    ON tasks(assigned_role_id)
                """))
                session.commit()
                logger.info("Column added successfully")
            else:
                logger.info("Column assigned_role_id already exists")
                
        except Exception as e:
            logger.error(f"Error adding column: {e}")
            session.rollback()
    
    logger.info("Organization tables created successfully")
    engine.dispose()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ORGANIZATION STRUCTURE TABLES MIGRATION")
    print("="*60)
    asyncio.run(create_tables())
    print("\n✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Load organization data: python app/scripts/load_organization.py")
    print("2. Restart the server: docker compose restart app")
    print("="*60 + "\n")

