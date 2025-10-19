"""Agent configuration models for dynamic agent management."""

from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Column, JSON
from app.models.base import BaseModel


class AgentConfiguration(BaseModel, table=True):
    """Configuration for AI agents.
    
    Allows dynamic configuration of agents through UI without code changes.
    Agents can be triggered based on categories, intents, keywords, or always.
    """
    
    __tablename__ = "agent_configurations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Agent identification
    agent_type: str = Field(
        max_length=50,
        index=True,
        description="Type of agent: classifier, intent, rag, react, role_assignment, etc"
    )
    name: str = Field(
        max_length=100,
        unique=True,
        index=True,
        description="Unique internal name (e.g., 'hr_specialist', 'it_support_l1')"
    )
    display_name: str = Field(
        max_length=100,
        description="Human-readable name displayed in UI"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Description of what this agent does"
    )
    
    # Trigger configuration - when to invoke this agent
    trigger_type: str = Field(
        max_length=50,
        index=True,
        description="When to trigger: 'always', 'category', 'intent', 'keyword', 'custom'"
    )
    trigger_value: dict = Field(
        default={},
        sa_column=Column(JSON),
        description="Trigger conditions: {'categories': ['hr', 'it'], 'keywords': [...], etc}"
    )
    
    # LLM Configuration
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt for this agent (can be multi-line)"
    )
    model: str = Field(
        default="openai/gpt-oss-120b",
        max_length=100,
        description="LLM model to use (e.g., 'openai/gpt-4', 'anthropic/claude-3.5-sonnet')"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM (0.0-2.0, lower = more deterministic)"
    )
    max_tokens: int = Field(
        default=2000,
        ge=100,
        le=32000,
        description="Maximum tokens for LLM response"
    )
    
    # Tool configuration
    enabled_tools: list[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="List of enabled tool IDs from tool registry (e.g., ['knowledge_search', 'calculator'])"
    )
    
    # Additional configuration (flexible JSON field)
    additional_config: dict = Field(
        default={},
        sa_column=Column(JSON),
        description="Additional config: qdrant_collection, response_format, tool_configs, etc"
    )
    
    # Status and priority
    is_active: bool = Field(
        default=True,
        index=True,
        description="Whether this agent is active and can be triggered"
    )
    priority: int = Field(
        default=0,
        description="Priority for agent execution (higher = called first when multiple agents match)"
    )
    
    # Metadata
    tags: list[str] = Field(
        default=[],
        sa_column=Column(JSON),
        description="Tags for categorizing agents (e.g., ['production', 'experimental'])"
    )
    
    # Performance tracking
    total_invocations: int = Field(
        default=0,
        description="Total number of times this agent was invoked"
    )
    avg_confidence: Optional[float] = Field(
        default=None,
        description="Average confidence score of agent responses"
    )
    last_invoked_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last invocation"
    )


class AgentInvocationLog(BaseModel, table=True):
    """Log of agent invocations for analytics and debugging."""
    
    __tablename__ = "agent_invocation_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Reference to agent
    agent_config_id: int = Field(
        foreign_key="agent_configurations.id",
        index=True,
        description="ID of the agent configuration used"
    )
    
    # Request context
    session_id: str = Field(
        max_length=100,
        index=True,
        description="Session ID for tracking conversations"
    )
    user_message: str = Field(
        description="User's original message"
    )
    
    # Classification context
    category: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Classified category"
    )
    intent: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Classified intent"
    )
    priority: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Classified priority"
    )
    
    # Agent response
    agent_response: Optional[str] = Field(
        default=None,
        description="Agent's response"
    )
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score of the response"
    )
    
    # Performance metrics
    execution_time_ms: Optional[int] = Field(
        default=None,
        description="Execution time in milliseconds"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        description="Number of tokens used"
    )
    
    # Status
    status: str = Field(
        default="success",
        max_length=20,
        description="Execution status: success, error, timeout"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if status is error"
    )

