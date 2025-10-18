"""ReAct Agent API endpoints.

This module provides endpoints for the ReAct agent that analyzes and solves
user problems after classification.
"""

from fastapi import APIRouter, HTTPException, Request, Depends

from app.core.config import settings
from app.core.langgraph.classifier import classification_agent
from app.core.langgraph.react_agent import get_react_agent
from app.core.limiter import limiter
from app.core.logging import logger
from app.schemas.agent_result import AgentAnalysisRequest, AgentAnalysisResponse, AgentResult
from app.schemas.classification import TicketCategory

router = APIRouter()


@router.post("/analyze", response_model=AgentAnalysisResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def analyze_problem(
    request: Request,
    analysis_request: AgentAnalysisRequest,
    session_id: str,
):
    """Analyze a user's problem with the ReAct agent.
    
    This endpoint:
    1. Classifies the user's message
    2. If category is NOT "other", runs the ReAct agent
    3. Returns a comprehensive analysis with classification and solution
    
    Args:
        request: FastAPI request object for rate limiting
        analysis_request: The analysis request containing the user's message
        session_id: The session ID for tracking
        
    Returns:
        AgentAnalysisResponse: The analysis result from the agent
        
    Raises:
        HTTPException: If classification or analysis fails
    """
    try:
        logger.info(
            "agent_analysis_request_received",
            session_id=session_id,
            message_length=len(analysis_request.message)
        )
        
        # Step 1: Classify the message
        classification = await classification_agent.classify(analysis_request.message)
        
        if classification is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to classify the message"
            )
        
        logger.info(
            "message_classified_for_agent",
            session_id=session_id,
            category=classification.category,
            priority=classification.priority
        )
        
        # Step 2: Check if category is NOT "other"
        if classification.category == TicketCategory.OTHER:
            logger.info(
                "skipping_react_agent_for_other_category",
                session_id=session_id
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Category is 'other'",
                    "message": "ReAct agent is only triggered for specific categories (HR, IT, Finance, Office)",
                    "classification": {
                        "category": classification.category,
                        "priority": classification.priority,
                        "reasoning": classification.reasoning,
                        "confidence": classification.confidence
                    }
                }
            )
        
        # Step 3: Run the ReAct agent
        logger.info(
            "starting_react_agent_analysis",
            session_id=session_id,
            category=classification.category
        )
        
        agent = get_react_agent()
        result = await agent.analyze_problem(
            user_message=analysis_request.message,
            classification=classification,
            session_id=session_id
        )
        
        logger.info(
            "react_agent_analysis_completed",
            session_id=session_id
        )
        
        return AgentAnalysisResponse(
            result=AgentResult(**result),
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "agent_analysis_error",
            error=str(e),
            session_id=session_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during analysis: {str(e)}"
        )


@router.post("/chat-with-classification", response_model=AgentAnalysisResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def chat_with_auto_classification(
    request: Request,
    analysis_request: AgentAnalysisRequest,
    session_id: str,
):
    """Chat endpoint that automatically classifies and triggers ReAct agent if needed.
    
    This is a convenience endpoint that combines classification and agent analysis.
    It's designed to be used in the chatbot flow:
    1. User sends a message
    2. Message is classified
    3. If NOT "other", ReAct agent is triggered automatically
    4. Result is returned with both classification and solution
    
    Args:
        request: FastAPI request object for rate limiting
        analysis_request: The analysis request containing the user's message
        session_id: The session ID for tracking
        
    Returns:
        AgentAnalysisResponse: The analysis result (only if category is NOT "other")
        
    Raises:
        HTTPException: If the category is "other" or if analysis fails
    """
    # This endpoint is identical to analyze_problem but with a different name
    # to make it clear it's intended for chatbot integration
    return await analyze_problem(request, analysis_request, session_id)

