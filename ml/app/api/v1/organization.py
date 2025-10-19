"""API endpoints for managing organizational structure."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlmodel import Session, select, func

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.services.database import get_db_session
from app.models.organization import OrganizationUnit, TaskCapabilityMapping
from pydantic import BaseModel, Field


# Schemas
class OrganizationUnitCreate(BaseModel):
    """Schema for creating an organization unit."""
    external_id: str = Field(..., max_length=200, description="Unique unit identifier")
    title: str = Field(..., max_length=500, description="Role title")
    position: Optional[str] = Field(None, max_length=500, description="Position name")
    unit_type: str = Field(..., max_length=50, description="Type: corporation, block, department, office, position")
    parent_id: Optional[int] = Field(None, description="Parent unit ID")
    description: Optional[str] = Field(None, max_length=2000, description="What this role does")


class OrganizationUnitUpdate(BaseModel):
    """Schema for updating an organization unit."""
    title: Optional[str] = Field(None, max_length=500)
    position: Optional[str] = Field(None, max_length=500)
    unit_type: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None


class CapabilityCreate(BaseModel):
    """Schema for creating a capability mapping."""
    unit_id: int = Field(..., description="Organization unit ID")
    category: str = Field(..., max_length=100, description="Category: IT, HR, Office, Finance")
    action_type: str = Field(..., max_length=200, description="What action/task this role can handle")
    keywords: List[str] = Field(default=[], description="Keywords for matching tasks")
    priority: int = Field(default=5, ge=1, le=10, description="Priority 1-10")


class CapabilityUpdate(BaseModel):
    """Schema for updating a capability mapping."""
    category: Optional[str] = Field(None, max_length=100)
    action_type: Optional[str] = Field(None, max_length=200)
    keywords: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=1, le=10)


class OrganizationUnitResponse(BaseModel):
    """Schema for organization unit response."""
    id: int
    external_id: str
    title: str
    position: Optional[str]
    unit_type: str
    parent_id: Optional[int]
    path: Optional[str]
    level: int
    description: Optional[str]
    is_active: bool
    capabilities_count: int = 0


class CapabilityResponse(BaseModel):
    """Schema for capability response."""
    id: int
    unit_id: int
    unit_title: str
    category: str
    action_type: str
    keywords: List[str]
    priority: int


router = APIRouter()


@router.post("/organization/units", response_model=OrganizationUnitResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_organization_unit(
    request: Request,
    unit: OrganizationUnitCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new organization unit (role/position)."""
    try:
        # Check if external_id already exists
        existing = db.exec(
            select(OrganizationUnit).where(OrganizationUnit.external_id == unit.external_id)
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail=f"Unit with ID '{unit.external_id}' already exists")
        
        # Calculate path and level based on parent
        path = unit.external_id
        level = 0
        
        if unit.parent_id:
            parent = db.get(OrganizationUnit, unit.parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail="Parent unit not found")
            path = f"{parent.path} > {unit.external_id}"
            level = parent.level + 1
        
        # Create organization unit
        new_unit = OrganizationUnit(
            external_id=unit.external_id,
            title=unit.title,
            position=unit.position,
            unit_type=unit.unit_type,
            parent_id=unit.parent_id,
            path=path,
            level=level,
            description=unit.description,
            is_active=True
        )
        
        db.add(new_unit)
        db.commit()
        db.refresh(new_unit)
        
        logger.info(
            "organization_unit_created",
            external_id=new_unit.external_id,
            title=new_unit.title,
            unit_type=new_unit.unit_type
        )
        
        # Count capabilities
        capabilities_count = db.exec(
            select(func.count(TaskCapabilityMapping.id))
            .where(TaskCapabilityMapping.handled_by_unit_id == new_unit.id)
        ).one()
        
        return OrganizationUnitResponse(
            id=new_unit.id,
            external_id=new_unit.external_id,
            title=new_unit.title,
            position=new_unit.position,
            unit_type=new_unit.unit_type,
            parent_id=new_unit.parent_id,
            path=new_unit.path,
            level=new_unit.level,
            description=new_unit.description,
            is_active=new_unit.is_active,
            capabilities_count=capabilities_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("organization_unit_creation_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organization/units", response_model=List[OrganizationUnitResponse])
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_organization_units(
    request: Request,
    unit_type: Optional[str] = None,
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db_session)
):
    """List all organization units with optional filtering."""
    try:
        query = select(OrganizationUnit).order_by(OrganizationUnit.path)
        
        if unit_type:
            query = query.where(OrganizationUnit.unit_type == unit_type)
        
        if parent_id is not None:
            query = query.where(OrganizationUnit.parent_id == parent_id)
        
        if is_active is not None:
            query = query.where(OrganizationUnit.is_active == is_active)
        
        units = db.exec(query).all()
        
        # Build response with capabilities count
        responses = []
        for unit in units:
            capabilities_count = db.exec(
                select(func.count(TaskCapabilityMapping.id))
                .where(TaskCapabilityMapping.handled_by_unit_id == unit.id)
            ).one()
            
            responses.append(OrganizationUnitResponse(
                id=unit.id,
                external_id=unit.external_id,
                title=unit.title,
                position=unit.position,
                unit_type=unit.unit_type,
                parent_id=unit.parent_id,
                path=unit.path,
                level=unit.level,
                description=unit.description,
                is_active=unit.is_active,
                capabilities_count=capabilities_count
            ))
        
        return responses
        
    except Exception as e:
        logger.error("list_organization_units_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organization/units/{unit_id}", response_model=OrganizationUnitResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_organization_unit(
    request: Request,
    unit_id: int,
    db: Session = Depends(get_db_session)
):
    """Get a specific organization unit by ID."""
    try:
        unit = db.get(OrganizationUnit, unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Organization unit not found")
        
        capabilities_count = db.exec(
            select(func.count(TaskCapabilityMapping.id))
            .where(TaskCapabilityMapping.handled_by_unit_id == unit.id)
        ).one()
        
        return OrganizationUnitResponse(
            id=unit.id,
            external_id=unit.external_id,
            title=unit.title,
            position=unit.position,
            unit_type=unit.unit_type,
            parent_id=unit.parent_id,
            path=unit.path,
            level=unit.level,
            description=unit.description,
            is_active=unit.is_active,
            capabilities_count=capabilities_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_organization_unit_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/organization/units/{unit_id}", response_model=OrganizationUnitResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def update_organization_unit(
    request: Request,
    unit_id: int,
    unit_update: OrganizationUnitUpdate,
    db: Session = Depends(get_db_session)
):
    """Update an organization unit."""
    try:
        unit = db.get(OrganizationUnit, unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Organization unit not found")
        
        # Update fields
        if unit_update.title is not None:
            unit.title = unit_update.title
        if unit_update.position is not None:
            unit.position = unit_update.position
        if unit_update.unit_type is not None:
            unit.unit_type = unit_update.unit_type
        if unit_update.description is not None:
            unit.description = unit_update.description
        if unit_update.is_active is not None:
            unit.is_active = unit_update.is_active
        if unit_update.parent_id is not None:
            unit.parent_id = unit_update.parent_id
            
            # Recalculate path and level
            if unit.parent_id:
                parent = db.get(OrganizationUnit, unit.parent_id)
                if parent:
                    unit.path = f"{parent.path} > {unit.external_id}"
                    unit.level = parent.level + 1
            else:
                unit.path = unit.external_id
                unit.level = 0
        
        db.add(unit)
        db.commit()
        db.refresh(unit)
        
        logger.info("organization_unit_updated", external_id=unit.external_id, title=unit.title)
        
        capabilities_count = db.exec(
            select(func.count(TaskCapabilityMapping.id))
            .where(TaskCapabilityMapping.handled_by_unit_id == unit.id)
        ).one()
        
        return OrganizationUnitResponse(
            id=unit.id,
            external_id=unit.external_id,
            title=unit.title,
            position=unit.position,
            unit_type=unit.unit_type,
            parent_id=unit.parent_id,
            path=unit.path,
            level=unit.level,
            description=unit.description,
            is_active=unit.is_active,
            capabilities_count=capabilities_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_organization_unit_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/organization/units/{unit_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_organization_unit(
    request: Request,
    unit_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete an organization unit."""
    try:
        unit = db.get(OrganizationUnit, unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Organization unit not found")
        
        # Check if unit has children
        children_count = db.exec(
            select(func.count(OrganizationUnit.id))
            .where(OrganizationUnit.parent_id == unit_id)
        ).one()
        
        if children_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete unit with {children_count} child units. Delete children first."
            )
        
        # Delete associated capabilities
        capabilities = db.exec(
            select(TaskCapabilityMapping)
            .where(TaskCapabilityMapping.handled_by_unit_id == unit_id)
        ).all()
        
        for cap in capabilities:
            db.delete(cap)
        
        db.delete(unit)
        db.commit()
        
        logger.info("organization_unit_deleted", external_id=unit.external_id, title=unit.title)
        
        return {"success": True, "message": f"Organization unit '{unit.title}' deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_organization_unit_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Capabilities endpoints

@router.post("/organization/capabilities", response_model=CapabilityResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_capability(
    request: Request,
    capability: CapabilityCreate,
    db: Session = Depends(get_db_session)
):
    """Add a capability to a role."""
    try:
        # Verify unit exists
        unit = db.get(OrganizationUnit, capability.unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Organization unit not found")
        
        # Create capability mapping
        new_capability = TaskCapabilityMapping(
            handled_by_unit_id=capability.unit_id,
            category=capability.category.lower(),
            action_type=capability.action_type,
            keywords=capability.keywords,
            priority=capability.priority
        )
        
        db.add(new_capability)
        db.commit()
        db.refresh(new_capability)
        
        logger.info(
            "capability_created",
            unit_id=capability.unit_id,
            unit_title=unit.title,
            action_type=capability.action_type
        )
        
        return CapabilityResponse(
            id=new_capability.id,
            unit_id=new_capability.handled_by_unit_id,
            unit_title=unit.title,
            category=new_capability.category,
            action_type=new_capability.action_type,
            keywords=new_capability.keywords,
            priority=new_capability.priority
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("capability_creation_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organization/capabilities", response_model=List[CapabilityResponse])
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_capabilities(
    request: Request,
    unit_id: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """List all capabilities with optional filtering."""
    try:
        query = select(TaskCapabilityMapping, OrganizationUnit).join(
            OrganizationUnit,
            TaskCapabilityMapping.handled_by_unit_id == OrganizationUnit.id
        )
        
        if unit_id:
            query = query.where(TaskCapabilityMapping.handled_by_unit_id == unit_id)
        
        if category:
            query = query.where(TaskCapabilityMapping.category == category.lower())
        
        results = db.exec(query).all()
        
        responses = []
        for capability, unit in results:
            responses.append(CapabilityResponse(
                id=capability.id,
                unit_id=capability.handled_by_unit_id,
                unit_title=unit.title,
                category=capability.category,
                action_type=capability.action_type,
                keywords=capability.keywords,
                priority=capability.priority
            ))
        
        return responses
        
    except Exception as e:
        logger.error("list_capabilities_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/organization/capabilities/{capability_id}", response_model=CapabilityResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def update_capability(
    request: Request,
    capability_id: int,
    capability_update: CapabilityUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a capability."""
    try:
        capability = db.get(TaskCapabilityMapping, capability_id)
        if not capability:
            raise HTTPException(status_code=404, detail="Capability not found")
        
        if capability_update.category is not None:
            capability.category = capability_update.category.lower()
        if capability_update.action_type is not None:
            capability.action_type = capability_update.action_type
        if capability_update.keywords is not None:
            capability.keywords = capability_update.keywords
        if capability_update.priority is not None:
            capability.priority = capability_update.priority
        
        db.add(capability)
        db.commit()
        db.refresh(capability)
        
        # Get unit for response
        unit = db.get(OrganizationUnit, capability.handled_by_unit_id)
        
        logger.info("capability_updated", capability_id=capability_id)
        
        return CapabilityResponse(
            id=capability.id,
            unit_id=capability.handled_by_unit_id,
            unit_title=unit.title if unit else "Unknown",
            category=capability.category,
            action_type=capability.action_type,
            keywords=capability.keywords,
            priority=capability.priority
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_capability_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/organization/capabilities/{capability_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_capability(
    request: Request,
    capability_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete a capability."""
    try:
        capability = db.get(TaskCapabilityMapping, capability_id)
        if not capability:
            raise HTTPException(status_code=404, detail="Capability not found")
        
        db.delete(capability)
        db.commit()
        
        logger.info("capability_deleted", capability_id=capability_id)
        
        return {"success": True, "message": "Capability deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_capability_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
