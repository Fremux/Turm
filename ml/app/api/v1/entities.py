"""API endpoints for managing extracted entities."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import select
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.entity import UserEntity
from app.schemas.entity import EntitiesListResponse, EntityResponse
from app.services.database import get_session as get_db_session
from app.core.config import settings

router = APIRouter()


@router.get("/entities", response_model=EntitiesListResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_user_entities(
    request: Request,
    user_id: int = 1,
    entity_type: Optional[str] = None,
    db = Depends(get_db_session)
):
    """Get all extracted entities for the current user.
    
    Args:
        request: The FastAPI request object for rate limiting
        user_id: The user ID
        entity_type: Optional filter by entity type
        db: Database session
        
    Returns:
        EntitiesListResponse: List of entities and total count
    """
    try:
        # Build query
        query = select(UserEntity).where(UserEntity.user_id == user_id)
        
        if entity_type:
            query = query.where(UserEntity.entity_type == entity_type)
        
        # Order by most recent first
        query = query.order_by(UserEntity.created_at.desc())
        
        result = db.execute(query)
        entities = result.scalars().all()
        
        return EntitiesListResponse(
            entities=[EntityResponse.model_validate(e) for e in entities],
            total=len(entities)
        )
        
    except Exception as e:
        logger.error("get_entities_failed", user_id=user_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/session/{session_id}", response_model=EntitiesListResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def get_session_entities(
    request: Request,
    session_id: str,
    user_id: int = 1,
    db = Depends(get_db_session)
):
    """Get all extracted entities for a specific session.
    
    Args:
        request: The FastAPI request object for rate limiting
        session_id: The session ID to get entities for
        user_id: The user ID
        db: Database session
        
    Returns:
        EntitiesListResponse: List of entities and total count
    """
    try:
        # Get entities for the session
        query = select(UserEntity).where(
            UserEntity.user_id == user_id,
            UserEntity.session_id == session_id
        ).order_by(UserEntity.created_at.desc())
        
        result = db.execute(query)
        entities = result.scalars().all()
        
        return EntitiesListResponse(
            entities=[EntityResponse.model_validate(e) for e in entities],
            total=len(entities)
        )
        
    except Exception as e:
        logger.error("get_session_entities_failed", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entities/{entity_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_entity(
    request: Request,
    entity_id: int,
    user_id: int = 1,
    db = Depends(get_db_session)
):
    """Delete a specific entity.
    
    Args:
        request: The FastAPI request object for rate limiting
        entity_id: The entity ID to delete
        user_id: The user ID
        db: Database session
        
    Returns:
        dict: Success message
    """
    try:
        # Find the entity and verify ownership
        query = select(UserEntity).where(
            UserEntity.id == entity_id,
            UserEntity.user_id == user_id
        )
        result = db.execute(query)
        entity = result.scalar_one_or_none()
        
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        db.delete(entity)
        db.commit()
        
        return {"message": "Entity deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_entity_failed", entity_id=entity_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

