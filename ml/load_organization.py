"""Load organization structure from users.json into database."""

import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select
from app.services.database import database_service
from app.models.organization import OrganizationUnit
from app.core.logging import logger


def load_unit_recursive(
    unit_data: dict,
    parent_id: Optional[int] = None,
    level: int = 0,
    parent_path: str = "",
    db: Session = None
) -> OrganizationUnit:
    """Recursively load organization unit and its children.
    
    Args:
        unit_data: Unit data from JSON
        parent_id: Parent unit ID
        level: Hierarchy level
        parent_path: Parent path for building full path
        db: Database session
        
    Returns:
        Created OrganizationUnit
    """
    # Build path
    path = f"{parent_path} > {unit_data['title']}" if parent_path else unit_data['title']
    
    # Check if unit already exists
    existing = db.exec(
        select(OrganizationUnit).where(OrganizationUnit.external_id == unit_data['id'])
    ).first()
    
    if existing:
        logger.info(f"Unit already exists: {unit_data['id']}")
        unit = existing
    else:
        # Create new unit
        unit = OrganizationUnit(
            external_id=unit_data['id'],
            title=unit_data['title'],
            position=unit_data.get('position'),
            unit_type=unit_data['unit_type'],
            description=unit_data.get('description'),
            parent_id=parent_id,
            level=level,
            path=path,
            capabilities={},
            is_active=True
        )
        db.add(unit)
        db.flush()  # Flush to get the ID
        logger.info(f"Created unit: {unit.external_id} (ID: {unit.id})")
    
    # Process children
    children = unit_data.get('children', [])
    for child_data in children:
        load_unit_recursive(
            child_data,
            parent_id=unit.id,
            level=level + 1,
            parent_path=path,
            db=db
        )
    
    return unit


def load_organization_structure(json_path: str = "users.json"):
    """Load organization structure from JSON file.
    
    Args:
        json_path: Path to users.json file
    """
    try:
        # Read JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            root_data = json.load(f)
        
        logger.info(f"Loaded organization structure from {json_path}")
        
        # Create database session
        with Session(database_service.engine) as db:
            # Check if organization already exists
            existing_count = db.exec(
                select(OrganizationUnit)
            ).first()
            
            if existing_count:
                logger.info("Organization structure already exists in database")
                response = input("Do you want to reload it? This will skip existing units (y/n): ")
                if response.lower() != 'y':
                    logger.info("Skipping organization structure load")
                    return
            
            # Load root unit recursively
            load_unit_recursive(root_data, parent_id=None, level=0, parent_path="", db=db)
            
            # Commit all changes
            db.commit()
            
            # Count loaded units
            total = db.exec(select(OrganizationUnit)).all()
            logger.info(f"✅ Successfully loaded {len(total)} organization units")
            
            # Show summary by type
            for unit_type in ['corporation', 'block', 'directorate', 'department', 'office', 'role', 'position']:
                count = len([u for u in total if u.unit_type == unit_type])
                if count > 0:
                    logger.info(f"  - {unit_type}: {count}")
    
    except FileNotFoundError:
        logger.error(f"❌ File not found: {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error loading organization structure: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  LOADING ORGANIZATION STRUCTURE")
    print("="*70 + "\n")
    
    load_organization_structure()
    
    print("\n" + "="*70)
    print("  ✅ DONE")
    print("="*70 + "\n")

