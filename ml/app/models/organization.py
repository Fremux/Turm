"""Organization structure models for role-based task assignment."""

from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, Column
from sqlalchemy import JSON
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.task import Task


class OrganizationUnit(BaseModel, table=True):
    """Represents a unit in the organization structure (role, department, etc)."""
    
    __tablename__ = "organization_units"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Original ID from users.json for reference
    external_id: str = Field(unique=True, index=True, max_length=200, description="ID from users.json")
    
    # Basic info
    title: str = Field(max_length=500, description="Title of the unit/role")
    position: Optional[str] = Field(default=None, max_length=500, description="Position title (e.g., 'Senior Developer')")
    unit_type: str = Field(max_length=50, index=True, description="Type: corporation, block, department, office, role, position, etc")
    description: Optional[str] = Field(default=None, max_length=2000, description="What this role does")
    
    # Hierarchy
    parent_id: Optional[int] = Field(default=None, foreign_key="organization_units.id", index=True)
    level: int = Field(default=0, description="Hierarchy level (0 = root)")
    
    # Full path for quick lookups (e.g., "rosatom-root > it-block > it-dept")
    path: Optional[str] = Field(default=None, max_length=2000)
    
    # Capabilities stored as JSON
    # Format: {"actions": ["создать доступ", "настроить оборудование"], "systems": ["AD", "VPN"]}
    capabilities: dict = Field(default={}, sa_column=Column(JSON), description="What this role can handle")
    
    # Activity status
    is_active: bool = Field(default=True, index=True)
    
    # Relationships
    tasks: list["Task"] = Relationship(back_populates="assigned_role")


class TaskCapabilityMapping(BaseModel, table=True):
    """Maps task categories/actions to organization units that can handle them."""
    
    __tablename__ = "task_capability_mappings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Task info
    category: str = Field(max_length=100, index=True, description="HR, IT, Finance, Office")
    action_type: str = Field(max_length=200, description="Type of action or system")
    keywords: list[str] = Field(default=[], sa_column=Column(JSON), description="Keywords for matching")
    
    # Who handles it
    handled_by_unit_id: int = Field(foreign_key="organization_units.id", index=True)
    escalate_to_unit_id: Optional[int] = Field(default=None, foreign_key="organization_units.id")
    
    # Priority/confidence
    priority: int = Field(default=5, description="Priority for selection (1-10, higher = more specific)")
    
    # Relationships
    handled_by: Optional[OrganizationUnit] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TaskCapabilityMapping.handled_by_unit_id]"}
    )
    escalate_to: Optional[OrganizationUnit] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TaskCapabilityMapping.escalate_to_unit_id]"}
    )


# Avoid circular imports
from app.models.task import Task

