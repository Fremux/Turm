"""Load organization structure from users.json into database."""

import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from sqlmodel import Session, select

from app.core.config import settings
from app.core.logging import logger
from app.services.database import database_service
from app.models.organization import OrganizationUnit, TaskCapabilityMapping


def load_users_json() -> Dict[str, Any]:
    """Load and parse users.json file."""
    users_json_path = Path(__file__).parent.parent.parent / "users.json"
    
    if not users_json_path.exists():
        raise FileNotFoundError(f"users.json not found at {users_json_path}")
    
    with open(users_json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def process_node(
    node: Dict[str, Any],
    session: Session,
    parent_id: Optional[int] = None,
    level: int = 0,
    path: str = ""
) -> Optional[OrganizationUnit]:
    """Recursively process a node in the organization tree."""
    
    external_id = node.get("id")
    if not external_id:
        return None
    
    # Check if unit already exists
    existing = session.exec(
        select(OrganizationUnit).where(OrganizationUnit.external_id == external_id)
    ).first()
    
    # Build path
    current_path = f"{path} > {node.get('title')}" if path else node.get("title")
    
    if existing:
        # Update existing
        existing.title = node.get("title", "")
        existing.position = node.get("position")
        existing.unit_type = node.get("unit_type", "unknown")
        existing.parent_id = parent_id
        existing.level = level
        existing.path = current_path
        unit = existing
        logger.debug(f"Updated unit: {external_id}")
    else:
        # Create new
        unit = OrganizationUnit(
            external_id=external_id,
            title=node.get("title", ""),
            position=node.get("position"),
            unit_type=node.get("unit_type", "unknown"),
            parent_id=parent_id,
            level=level,
            path=current_path,
            capabilities={},
            is_active=True
        )
        session.add(unit)
        logger.debug(f"Created unit: {external_id}")
    
    session.commit()
    session.refresh(unit)
    
    # Process children
    children = node.get("children", [])
    for child in children:
        process_node(child, session, parent_id=unit.id, level=level + 1, path=current_path)
    
    return unit


def create_capability_mappings(task_coverage: Dict[str, Any], session: Session):
    """Create task capability mappings from task_coverage data."""
    
    logger.info("Creating task capability mappings...")
    
    # Clear existing mappings
    session.query(TaskCapabilityMapping).delete()
    
    for category, coverage_data in task_coverage.items():
        logger.info(f"Processing category: {category}")
        
        # Process actions
        actions = coverage_data.get("actions", {})
        for action, mapping_data in actions.items():
            handled_by_id = mapping_data.get("handled_by_id")
            
            if not handled_by_id:
                continue
            
            # Find the organization unit
            unit = session.exec(
                select(OrganizationUnit).where(OrganizationUnit.external_id == handled_by_id)
            ).first()
            
            if not unit:
                logger.warning(f"Unit not found: {handled_by_id}")
                continue
            
            # Extract keywords from action
            keywords = [word.strip() for word in action.lower().split("/")]
            
            # Get escalation unit if specified
            escalate_to_id_str = mapping_data.get("escalate_to_id")
            escalate_to_unit_id = None
            if escalate_to_id_str:
                escalate_unit = session.exec(
                    select(OrganizationUnit).where(OrganizationUnit.external_id == escalate_to_id_str)
                ).first()
                if escalate_unit:
                    escalate_to_unit_id = escalate_unit.id
            
            # Create mapping
            mapping = TaskCapabilityMapping(
                category=category.lower(),
                action_type=action,
                keywords=keywords,
                handled_by_unit_id=unit.id,
                escalate_to_unit_id=escalate_to_unit_id,
                priority=7  # Actions are high priority
            )
            session.add(mapping)
        
        # Process systems/entities
        systems = coverage_data.get("systems", coverage_data.get("entities", {}))
        for system_name, mapping_data in systems.items():
            handled_by_id = mapping_data.get("handled_by_id")
            
            if not handled_by_id:
                continue
            
            # Find the organization unit
            unit = session.exec(
                select(OrganizationUnit).where(OrganizationUnit.external_id == handled_by_id)
            ).first()
            
            if not unit:
                logger.warning(f"Unit not found: {handled_by_id}")
                continue
            
            # Extract keywords
            keywords = [word.strip() for word in system_name.lower().split("/")]
            
            # Get escalation/coordination unit if specified
            escalate_to_id_str = mapping_data.get("escalate_to_id") or mapping_data.get("coord_with_id")
            escalate_to_unit_id = None
            if escalate_to_id_str:
                escalate_unit = session.exec(
                    select(OrganizationUnit).where(OrganizationUnit.external_id == escalate_to_id_str)
                ).first()
                if escalate_unit:
                    escalate_to_unit_id = escalate_unit.id
            
            # Create mapping
            mapping = TaskCapabilityMapping(
                category=category.lower(),
                action_type=system_name,
                keywords=keywords,
                handled_by_unit_id=unit.id,
                escalate_to_unit_id=escalate_to_unit_id,
                priority=5  # Systems are medium priority
            )
            session.add(mapping)
    
    session.commit()
    logger.info("Task capability mappings created")


async def load_organization_data():
    """Main function to load organization data."""
    try:
        logger.info("Loading organization structure from users.json...")
        
        # Load JSON data
        data = load_users_json()
        
        # Get database session
        session = Session(database_service.engine)
        
        # Process the root node and all children
        root_node = data
        process_node(root_node, session)
        
        # Create capability mappings from task_coverage
        task_coverage = data.get("task_coverage", {})
        if task_coverage:
            create_capability_mappings(task_coverage, session)
        
        # Get statistics
        total_units = session.query(OrganizationUnit).count()
        total_mappings = session.query(TaskCapabilityMapping).count()
        
        logger.info(f"✅ Organization structure loaded successfully!")
        logger.info(f"   - Total units: {total_units}")
        logger.info(f"   - Total capability mappings: {total_mappings}")
        
        # Show sample units by type
        for unit_type in ["corporation", "block", "department", "office", "position"]:
            count = session.query(OrganizationUnit).filter(
                OrganizationUnit.unit_type == unit_type
            ).count()
            if count > 0:
                logger.info(f"   - {unit_type.capitalize()}s: {count}")
        
        session.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading organization data: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LOADING ORGANIZATION STRUCTURE FROM users.json")
    print("="*70 + "\n")
    
    success = asyncio.run(load_organization_data())
    
    if success:
        print("\n✅ Organization data loaded successfully!")
        print("\nYou can now:")
        print("1. Create tasks and they will be auto-assigned to roles")
        print("2. View role assignments in admin panel")
        print("3. Query organization structure via API")
    else:
        print("\n❌ Failed to load organization data. Check logs for details.")
    
    print("\n" + "="*70 + "\n")

