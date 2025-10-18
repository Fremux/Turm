"""API endpoints for managing agent analyses."""

from typing import List
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlmodel import select

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.agent_analysis import AgentAnalysis
from app.schemas.agent_result import AgentResult
from app.services.database import get_session as get_db_session

router = APIRouter()


@router.get("/analyses", response_model=List[AgentResult])
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
def get_user_analyses(
    request: Request,
    user_id: int,
    session_id: str = None,
    db = Depends(get_db_session)
):
    """Get all agent analyses for a user, optionally filtered by session.
    
    Args:
        request: FastAPI request object for rate limiting
        user_id: The user ID to get analyses for
        session_id: Optional session ID to filter by
        db: Database session
        
    Returns:
        List of agent analysis results
        
    Raises:
        HTTPException: If there's an error retrieving analyses
    """
    try:
        logger.info(
            "get_analyses_request",
            user_id=user_id,
            session_id=session_id
        )
        
        # Build query
        query = select(AgentAnalysis).where(AgentAnalysis.user_id == user_id)
        if session_id:
            query = query.where(AgentAnalysis.session_id == session_id)
        
        # Order by most recent first
        query = query.order_by(AgentAnalysis.created_at.desc())
        
        # Execute query (sync)
        analyses = db.exec(query).all()
        
        # Convert to response format
        response = []
        for analysis in analyses:
            response.append(AgentResult(
                classification={
                    "category": analysis.category,
                    "priority": analysis.priority,
                    "reasoning": analysis.reasoning,
                    "confidence": analysis.confidence
                },
                session_id=analysis.session_id,
                summary=analysis.summary,
                solution=analysis.solution,
                problem=analysis.problem
            ))
        
        logger.info(
            "get_analyses_success",
            user_id=user_id,
            count=len(response)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "get_analyses_failed",
            error=str(e),
            user_id=user_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analyses: {str(e)}"
        )


@router.get("/analyses/{analysis_id}", response_model=AgentResult)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
def get_analysis(
    request: Request,
    analysis_id: int,
    user_id: int,
    db = Depends(get_db_session)
):
    """Get a specific agent analysis by ID.
    
    Args:
        request: FastAPI request object for rate limiting
        analysis_id: The analysis ID
        user_id: The user ID (for security check)
        db: Database session
        
    Returns:
        The agent analysis result
        
    Raises:
        HTTPException: If analysis not found or access denied
    """
    try:
        # Get analysis (sync)
        query = select(AgentAnalysis).where(
            AgentAnalysis.id == analysis_id,
            AgentAnalysis.user_id == user_id
        )
        analysis = db.exec(query).first()
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found or access denied"
            )
        
        return AgentResult(
            classification={
                "category": analysis.category,
                "priority": analysis.priority,
                "reasoning": analysis.reasoning,
                "confidence": analysis.confidence
            },
            session_id=analysis.session_id,
            summary=analysis.summary,
            solution=analysis.solution,
            problem=analysis.problem
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_analysis_failed",
            error=str(e),
            analysis_id=analysis_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analysis: {str(e)}"
        )

