"""Schemas for agent configuration API."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AgentConfigBase(BaseModel):
    """Base schema for agent configuration."""
    
    agent_type: str = Field(..., min_length=1, max_length=50, description="Type of agent")
    name: str = Field(..., min_length=1, max_length=100, description="Unique internal name")
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, max_length=500, description="Agent description")
    
    # Trigger configuration
    trigger_type: str = Field(..., description="Trigger type: always, category, intent, keyword")
    trigger_value: dict = Field(default={}, description="Trigger conditions")
    
    # LLM configuration
    system_prompt: Optional[str] = Field(None, description="System prompt for the agent")
    model: str = Field(default="openai/gpt-oss-120b", max_length=100, description="LLM model")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=2000, ge=100, le=32000, description="Max tokens")
    
    # Additional config
    additional_config: dict = Field(default={}, description="Additional configuration")
    
    # Status
    is_active: bool = Field(default=True, description="Whether agent is active")
    priority: int = Field(default=0, description="Execution priority (higher = first)")
    tags: list[str] = Field(default=[], description="Tags for categorization")


class AgentConfigCreate(AgentConfigBase):
    """Schema for creating a new agent configuration."""
    pass


class AgentConfigUpdate(BaseModel):
    """Schema for updating an agent configuration."""
    
    agent_type: Optional[str] = Field(None, min_length=1, max_length=50)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    # Trigger configuration
    trigger_type: Optional[str] = None
    trigger_value: Optional[dict] = None
    
    # LLM configuration
    system_prompt: Optional[str] = None
    model: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=32000)
    
    # Additional config
    additional_config: Optional[dict] = None
    
    # Status
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    tags: Optional[list[str]] = None


class AgentConfigResponse(AgentConfigBase):
    """Schema for agent configuration response."""
    
    id: int
    created_at: datetime
    
    # Performance metrics
    total_invocations: int = Field(default=0, description="Total invocations")
    avg_confidence: Optional[float] = Field(None, description="Average confidence")
    last_invoked_at: Optional[datetime] = Field(None, description="Last invocation time")
    
    class Config:
        from_attributes = True


class AgentConfigListResponse(BaseModel):
    """Response for list of agent configurations."""
    
    agents: list[AgentConfigResponse]
    total: int


class AgentTestRequest(BaseModel):
    """Request to test an agent."""
    
    message: str = Field(..., min_length=1, max_length=2000, description="Test message")
    category: Optional[str] = Field(None, description="Category context")
    intent: Optional[str] = Field(None, description="Intent context")
    priority: Optional[str] = Field(None, description="Priority context")


class AgentTestResponse(BaseModel):
    """Response from testing an agent."""
    
    agent_id: int
    agent_name: str
    triggered: bool = Field(..., description="Whether agent was triggered")
    response: Optional[str] = Field(None, description="Agent response")
    confidence: Optional[float] = Field(None, description="Confidence score")
    execution_time_ms: Optional[int] = Field(None, description="Execution time")
    error: Optional[str] = Field(None, description="Error message if failed")


class AgentInvocationLogResponse(BaseModel):
    """Response for agent invocation log."""
    
    id: int
    agent_config_id: int
    session_id: str
    user_message: str
    category: Optional[str]
    intent: Optional[str]
    priority: Optional[str]
    agent_response: Optional[str]
    confidence: Optional[float]
    execution_time_ms: Optional[int]
    tokens_used: Optional[int]
    status: str
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentStatsResponse(BaseModel):
    """Statistics for an agent."""
    
    agent_id: int
    agent_name: str
    total_invocations: int
    success_count: int
    error_count: int
    avg_confidence: Optional[float]
    avg_execution_time_ms: Optional[float]
    last_invoked_at: Optional[datetime]

