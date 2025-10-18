"""Agent Analysis model for storing ReAct agent results."""

from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, Column, Text
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class AgentAnalysis(BaseModel, table=True):
    """Model for storing ReAct agent analysis results.
    
    Attributes:
        id: The primary key
        user_id: Foreign key to the user
        session_id: The session where this analysis was performed
        problem: The original problem description from user
        category: Classification category (hr, it, finance, office)
        priority: Classification priority (low, medium, high, urgent)
        confidence: Classification confidence score (0-1)
        reasoning: Classification reasoning
        solution: The solution provided by the agent
        summary: Full summary of the analysis
        created_at: When the analysis was created
    """
    
    __tablename__ = "agent_analysis"
    
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    session_id: str = Field(index=True)
    
    # Problem details
    problem: str = Field(sa_column=Column(Text))
    
    # Classification
    category: str = Field(max_length=50, index=True)
    priority: str = Field(max_length=50, index=True)
    confidence: float = Field(default=0.0)
    reasoning: str = Field(default="", max_length=500)
    
    # Solution
    solution: str = Field(sa_column=Column(Text))
    summary: str = Field(sa_column=Column(Text))
    
    # Relationship
    user: Optional["User"] = Relationship(back_populates="agent_analyses")


# Avoid circular imports
from app.models.user import User  # noqa: E402

