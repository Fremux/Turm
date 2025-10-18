"""Classification endpoints for support ticket classification."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.langgraph.classifier import classification_agent
from app.core.langgraph.intent_classifier import intent_classification_agent
from app.core.langgraph.role_assignment_agent import role_assignment_agent
from app.core.limiter import limiter
from app.core.logging import logger
from app.schemas.classification import TicketClassification, IntentClassification, RoleAssignment

router = APIRouter()


class ClassifyRequest(BaseModel):
    """Request model for classification."""
    
    message: str = Field(..., description="The message to classify", min_length=1, max_length=2000)


class ClassifyResponse(BaseModel):
    """Response model for classification."""
    
    classification: TicketClassification = Field(..., description="The classification result")


class IntentClassifyResponse(BaseModel):
    """Response model for intent classification."""
    
    classification: IntentClassification = Field(..., description="The intent classification result")


class RoleAssignRequest(BaseModel):
    """Request model for role assignment."""
    
    message: str = Field(..., description="The message to analyze", min_length=1, max_length=2000)
    domain: str | None = Field(None, description="The department domain (HR/IT/Finance/Office)")
    intent: str | None = Field(None, description="The user intent type")


class RoleAssignResponse(BaseModel):
    """Response model for role assignment."""
    
    assignment: RoleAssignment | None = Field(None, description="The role assignment result")


@router.post("/classify", response_model=ClassifyResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def classify_message(
    request: Request,
    classify_request: ClassifyRequest,
    session_id: str
):
    """Classify a support ticket message.
    
    Args:
        request: FastAPI request object for rate limiting
        classify_request: The classification request
        session_id: The session ID
        
    Returns:
        ClassifyResponse: The classification result
        
    Raises:
        HTTPException: If classification fails
    """
    try:
        logger.info(
            "classification_request_received",
            session_id=session_id,
            message_length=len(classify_request.message)
        )
        
        # Classify the message
        classification = await classification_agent.classify(classify_request.message)
        
        if classification is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to classify message"
            )
        
        return ClassifyResponse(classification=classification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "classification_endpoint_error",
            error=str(e),
            session_id=session_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during classification"
        )


@router.post("/classify-intent", response_model=IntentClassifyResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def classify_intent(
    request: Request,
    classify_request: ClassifyRequest,
    session_id: str
):
    """Classify user intent.
    
    Args:
        request: FastAPI request object for rate limiting
        classify_request: The classification request
        session_id: The session ID
        
    Returns:
        IntentClassifyResponse: The intent classification result
        
    Raises:
        HTTPException: If classification fails
    """
    try:
        logger.info(
            "intent_classification_request_received",
            session_id=session_id,
            message_length=len(classify_request.message)
        )
        
        # Classify the intent
        classification = await intent_classification_agent.classify(classify_request.message)
        
        if classification is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to classify intent"
            )
        
        return IntentClassifyResponse(classification=classification)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "intent_classification_endpoint_error",
            error=str(e),
            session_id=session_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during intent classification"
        )


@router.post("/assign-role", response_model=RoleAssignResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["messages"][0])
async def assign_role(
    request: Request,
    assign_request: RoleAssignRequest,
    session_id: str
):
    """Assign appropriate role for handling the request.
    
    Args:
        request: FastAPI request object for rate limiting
        assign_request: The role assignment request
        session_id: The session ID
        
    Returns:
        RoleAssignResponse: The role assignment result
        
    Raises:
        HTTPException: If assignment fails
    """
    try:
        logger.info(
            "role_assignment_request_received",
            session_id=session_id,
            message_length=len(assign_request.message),
            domain=assign_request.domain,
            intent=assign_request.intent
        )
        
        # Assign role
        assignment = await role_assignment_agent.assign_role(
            assign_request.message,
            domain=assign_request.domain,
            intent=assign_request.intent
        )
        
        return RoleAssignResponse(assignment=assignment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "role_assignment_endpoint_error",
            error=str(e),
            session_id=session_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during role assignment"
        )

