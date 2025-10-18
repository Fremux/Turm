"""Classification schemas for support ticket classification."""

from enum import Enum
from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    """Support ticket categories by department.
    
    HR: Employee-related matters including payroll, benefits, time off, employee portal access, training/LMS.
    IT: System access, software, network, email, DevOps, infrastructure, technical issues.
    Finance: Accounting, taxes, payments, electronic document management (EDO), ERP systems.
    Office: Physical office services including passes, parking, meeting rooms, workspace setup, guest services, telephony.
    Other: Requests that don't fit into any specific department category.
    """
    
    HR = "hr"
    IT = "it"
    FINANCE = "finance"
    OFFICE = "office"
    OTHER = "other"


class TicketPriority(str, Enum):
    """Support ticket priority levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class IntentType(str, Enum):
    """User intent types."""
    
    ACCESS_REQUEST = "access_request"
    INFORMATION_REQUEST = "information_request"
    PROBLEM_SOLVING = "problem_solving"
    OTHER = "other"


class TicketClassification(BaseModel):
    """Classification result for a support ticket."""
    
    category: TicketCategory = Field(..., description="The category of the support ticket")
    priority: TicketPriority = Field(..., description="The priority level of the ticket")
    reasoning: str = Field(..., description="Brief explanation of the classification", max_length=500)
    confidence: float = Field(..., description="Confidence score (0-1)", ge=0.0, le=1.0)


class IntentClassification(BaseModel):
    """Intent classification result for a user request."""
    
    intent: IntentType = Field(..., description="The type of user intent")
    reasoning: str = Field(..., description="Brief explanation of the classification", max_length=500)
    confidence: float = Field(..., description="Confidence score (0-1)", ge=0.0, le=1.0)


class RoleInfo(BaseModel):
    """Information about a role in the organization."""
    
    id: str = Field(..., description="Role ID")
    title: str = Field(..., description="Role title")
    position: str | None = Field(None, description="Position name")
    path: list[str] = Field(..., description="Path in organizational hierarchy")


class RoleAssignment(BaseModel):
    """Role assignment result for handling a request."""
    
    domain: str | None = Field(None, description="The domain (HR/IT/Finance/Office)")
    matched_key: str | None = Field(None, description="The matched key from task coverage")
    primary_role: RoleInfo | None = Field(None, description="Primary role to handle the request")
    escalation_role: RoleInfo | None = Field(None, description="Escalation role if needed")
    coordination_role: RoleInfo | None = Field(None, description="Coordination role if needed")
    alternatives: list[dict] | None = Field(None, description="Alternative role assignments")
    confidence: float = Field(..., description="Confidence score (0-1)", ge=0.0, le=1.0)
    reason: str = Field(..., description="Brief explanation of the assignment", max_length=500)


class ClassificationResponse(BaseModel):
    """Response containing classification and chatbot response."""
    
    classification: TicketClassification = Field(..., description="The ticket classification")
    response: str = Field(..., description="The chatbot's response to the user")

