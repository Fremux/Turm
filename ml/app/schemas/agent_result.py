"""Schema for ReAct Agent results."""

from typing import Dict, Any
from pydantic import BaseModel, Field

from app.schemas.classification import TicketClassification


class AgentResult(BaseModel):
    """Result from the ReAct agent analysis.
    
    This schema contains the complete analysis result including:
    - The original problem classification
    - The session ID for tracking
    - A summary of the problem and solution
    """
    
    classification: Dict[str, Any] = Field(
        ...,
        description="The classification of the problem (category, priority, reasoning, confidence)"
    )
    session_id: str = Field(
        ...,
        description="The session ID for this analysis"
    )
    summary: str = Field(
        ...,
        description="A comprehensive summary of the problem analysis and solution"
    )
    solution: str = Field(
        ...,
        description="The detailed solution provided by the agent"
    )
    problem: str = Field(
        ...,
        description="The original problem description from the user"
    )


class AgentAnalysisRequest(BaseModel):
    """Request to analyze a problem with the ReAct agent."""
    
    message: str = Field(
        ...,
        description="The user's message describing the problem",
        min_length=1,
        max_length=5000
    )


class AgentAnalysisResponse(BaseModel):
    """Response from the ReAct agent analysis."""
    
    result: AgentResult = Field(
        ...,
        description="The analysis result from the agent"
    )
    success: bool = Field(
        default=True,
        description="Whether the analysis was successful"
    )

