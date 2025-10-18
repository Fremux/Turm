"""Entity schemas for API responses."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class EntityResponse(BaseModel):
    """Response model for a single entity.
    
    Attributes:
        id: The entity ID
        entity_type: Type of entity
        entity_value: The value of the entity
        context: Additional context
        confidence: Confidence score
        created_at: When the entity was extracted
    """
    
    id: int
    entity_type: str
    entity_value: str
    context: Optional[str] = None
    confidence: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class EntitiesListResponse(BaseModel):
    """Response model for list of entities.
    
    Attributes:
        entities: List of entities
        total: Total count of entities
    """
    
    entities: List[EntityResponse]
    total: int

