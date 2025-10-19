"""Add description field to organization_units table."""

import asyncio
from sqlmodel import create_engine, Session, text

from app.core.config import settings
from app.core.logging import logger


async def add_description_field():
    """Add description column to organization_units table."""
    print("\n" + "=" * 60)
    print("ADD DESCRIPTION TO ORGANIZATION UNITS")
    print("=" * 60)
    
    try:
        connection_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        engine = create_engine(connection_url, echo=False)
        
        with Session(engine) as session:
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='organization_units' 
                AND column_name='description'
            """)
            
            result = session.exec(check_query).first()
            
            if result:
                logger.info("description column already exists, skipping")
                print("✓ Description column already exists")
                return
            
            # Add description column
            logger.info("Adding description column to organization_units...")
            add_column_query = text("""
                ALTER TABLE organization_units 
                ADD COLUMN description VARCHAR(2000)
            """)
            
            session.exec(add_column_query)
            session.commit()
            
            logger.info("Description column added successfully")
            print("✓ Description column added successfully")
        
        engine.dispose()
        print("\n✅ Migration completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
        print(f"\n❌ Migration failed: {e}")
        print("=" * 60 + "\n")
        raise


if __name__ == "__main__":
    asyncio.run(add_description_field())




