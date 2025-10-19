"""API endpoints for classification corrections and examples."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlmodel import Session, select
from datetime import datetime

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.classification_correction import (
    ClassificationCorrection,
    ClassificationExample
)
from app.core.langgraph.classifier import classification_agent
from app.schemas.classification_correction import (
    ClassificationCorrectionCreate,
    ClassificationCorrectionResponse,
    ClassificationCorrectionListResponse,
    ClassificationExampleCreate,
    ClassificationExampleUpdate,
    ClassificationExampleResponse,
    ClassificationExampleListResponse
)
from app.services.database import get_session as get_db_session

router = APIRouter()


# Classification Corrections Endpoints

@router.post("/corrections", response_model=ClassificationCorrectionResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_correction(
    request: Request,
    correction: ClassificationCorrectionCreate,
    db: Session = Depends(get_db_session)
):
    """Create a classification correction from user feedback.
    
    When a user corrects a classification, we store it for future improvement.
    """
    try:
        new_correction = ClassificationCorrection(
            user_message=correction.user_message,
            session_id=correction.session_id,
            user_id=correction.user_id,
            predicted_category=correction.predicted_category,
            predicted_intent=correction.predicted_intent,
            predicted_priority=correction.predicted_priority,
            correct_category=correction.correct_category,
            correct_intent=correction.correct_intent,
            correct_priority=correction.correct_priority,
            notes=correction.notes,
            correction_type="manual"
        )
        
        db.add(new_correction)
        db.commit()
        db.refresh(new_correction)
        
        logger.info(
            "classification_correction_created",
            correction_id=new_correction.id,
            user_id=correction.user_id,
            predicted_category=correction.predicted_category,
            correct_category=correction.correct_category
        )
        
        # Refresh classifier to include new correction in few-shot examples
        classification_agent.refresh_categories()
        
        return ClassificationCorrectionResponse.from_orm(new_correction)
        
    except Exception as e:
        logger.error("create_correction_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create correction")


@router.get("/corrections", response_model=ClassificationCorrectionListResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_corrections(
    request: Request,
    category: Optional[str] = Query(default=None),
    intent: Optional[str] = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0),
    db: Session = Depends(get_db_session)
):
    """List classification corrections."""
    try:
        query = select(ClassificationCorrection)
        
        if active_only:
            query = query.where(ClassificationCorrection.is_active == True)
        if category:
            query = query.where(ClassificationCorrection.correct_category == category)
        if intent:
            query = query.where(ClassificationCorrection.correct_intent == intent)
        
        query = query.order_by(ClassificationCorrection.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        corrections = db.exec(query).all()
        
        # Get total count
        count_query = select(ClassificationCorrection)
        if active_only:
            count_query = count_query.where(ClassificationCorrection.is_active == True)
        if category:
            count_query = count_query.where(ClassificationCorrection.correct_category == category)
        if intent:
            count_query = count_query.where(ClassificationCorrection.correct_intent == intent)
        
        total = len(db.exec(count_query).all())
        
        responses = [ClassificationCorrectionResponse.from_orm(c) for c in corrections]
        
        return ClassificationCorrectionListResponse(corrections=responses, total=total)
        
    except Exception as e:
        logger.error("list_corrections_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list corrections")


@router.delete("/corrections/{correction_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_correction(
    request: Request,
    correction_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete a classification correction."""
    correction = db.get(ClassificationCorrection, correction_id)
    if not correction:
        raise HTTPException(status_code=404, detail="Correction not found")
    
    db.delete(correction)
    db.commit()
    
    logger.info("correction_deleted", correction_id=correction_id)
    
    # Refresh classifier after deletion
    classification_agent.refresh_categories()
    
    return {"message": "Correction deleted successfully"}


# Classification Examples Endpoints

@router.post("/examples", response_model=ClassificationExampleResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def create_example(
    request: Request,
    example: ClassificationExampleCreate,
    db: Session = Depends(get_db_session)
):
    """Create a classification example for few-shot learning."""
    try:
        new_example = ClassificationExample(
            example_text=example.example_text,
            category=example.category,
            intent=example.intent,
            priority=example.priority,
            reasoning=example.reasoning,
            source=example.source or "manual",
            priority_order=example.priority_order,
            example_type="manual"
        )
        
        db.add(new_example)
        db.commit()
        db.refresh(new_example)
        
        logger.info(
            "classification_example_created",
            example_id=new_example.id,
            category=example.category,
            intent=example.intent
        )
        
        # Refresh classifier to include new example
        classification_agent.refresh_categories()
        
        return ClassificationExampleResponse.from_orm(new_example)
        
    except Exception as e:
        logger.error("create_example_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create example")


@router.get("/examples", response_model=ClassificationExampleListResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def list_examples(
    request: Request,
    category: Optional[str] = Query(default=None),
    intent: Optional[str] = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0),
    db: Session = Depends(get_db_session)
):
    """List classification examples."""
    try:
        query = select(ClassificationExample)
        
        if active_only:
            query = query.where(ClassificationExample.is_active == True)
        if category:
            query = query.where(ClassificationExample.category == category)
        if intent:
            query = query.where(ClassificationExample.intent == intent)
        
        query = query.order_by(
            ClassificationExample.priority_order.desc(),
            ClassificationExample.created_at.desc()
        )
        query = query.offset(offset).limit(limit)
        
        examples = db.exec(query).all()
        
        # Get total count
        count_query = select(ClassificationExample)
        if active_only:
            count_query = count_query.where(ClassificationExample.is_active == True)
        if category:
            count_query = count_query.where(ClassificationExample.category == category)
        if intent:
            count_query = count_query.where(ClassificationExample.intent == intent)
        
        total = len(db.exec(count_query).all())
        
        responses = [ClassificationExampleResponse.from_orm(e) for e in examples]
        
        return ClassificationExampleListResponse(examples=responses, total=total)
        
    except Exception as e:
        logger.error("list_examples_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list examples")


@router.patch("/examples/{example_id}", response_model=ClassificationExampleResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def update_example(
    request: Request,
    example_id: int,
    example_update: ClassificationExampleUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a classification example."""
    example = db.get(ClassificationExample, example_id)
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    
    # Update fields
    update_data = example_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(example, key, value)
    
    db.add(example)
    db.commit()
    db.refresh(example)
    
    logger.info("example_updated", example_id=example_id)
    
    # Refresh classifier after update
    classification_agent.refresh_categories()
    
    return ClassificationExampleResponse.from_orm(example)


@router.delete("/examples/{example_id}")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def delete_example(
    request: Request,
    example_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete a classification example."""
    example = db.get(ClassificationExample, example_id)
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    
    db.delete(example)
    db.commit()
    
    logger.info("example_deleted", example_id=example_id)
    
    # Refresh classifier after deletion
    classification_agent.refresh_categories()
    
    return {"message": "Example deleted successfully"}


@router.post("/corrections/{correction_id}/promote")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def promote_correction_to_example(
    request: Request,
    correction_id: int,
    db: Session = Depends(get_db_session)
):
    """Promote a correction to a curated example."""
    correction = db.get(ClassificationCorrection, correction_id)
    if not correction:
        raise HTTPException(status_code=404, detail="Correction not found")
    
    # Create example from correction
    new_example = ClassificationExample(
        example_text=correction.user_message,
        category=correction.correct_category or correction.predicted_category,
        intent=correction.correct_intent or correction.predicted_intent,
        priority=correction.correct_priority or correction.predicted_priority,
        reasoning=f"Corrected from: {correction.predicted_category} → {correction.correct_category}",
        source=f"correction_{correction_id}",
        example_type="from_correction",
        priority_order=0
    )
    
    db.add(new_example)
    db.commit()
    db.refresh(new_example)
    
    logger.info(
        "correction_promoted_to_example",
        correction_id=correction_id,
        example_id=new_example.id
    )
    
    # Refresh classifier to include new example
    classification_agent.refresh_categories()
    
    return ClassificationExampleResponse.from_orm(new_example)

