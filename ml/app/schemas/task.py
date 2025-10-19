"""Schemas for task management."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Task Schemas
class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    
    summary: str = Field(..., description="Brief task description (5-7 words)", min_length=5, max_length=200)
    description: str = Field(..., description="Detailed task description", min_length=10, max_length=2000)
    assignee: str = Field(default="сотрудник", description="Who should complete the task", max_length=100)
    category_id: Optional[int] = Field(None, description="Category ID")
    priority: str = Field(default="medium", description="Priority level")
    original_message: Optional[str] = Field(None, description="Original user message", max_length=1000)
    created_by: Optional[int] = Field(None, description="Creator user ID")


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    
    summary: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    assignee: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=20)
    priority: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=2000)
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = Field(None, max_length=100)


class TaskResponse(BaseModel):
    """Schema for task response."""
    
    id: int
    summary: str
    description: str
    assignee: str
    status: str
    priority: str
    category_id: Optional[int]
    category_name: Optional[str] = None
    assigned_role_id: Optional[int] = None
    assigned_role_title: Optional[str] = None
    assigned_role_position: Optional[str] = None
    created_by: Optional[int]
    original_message: Optional[str]
    completed_at: Optional[datetime]
    completed_by: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class TasksListResponse(BaseModel):
    """Response for list of tasks."""
    
    tasks: list[TaskResponse]
    total: int


class TaskExtractionRequest(BaseModel):
    """Request for extracting task information from user message."""
    
    message: str = Field(..., description="User message requesting task creation")
    category: Optional[str] = Field(None, description="Detected category")
    user_id: Optional[int] = Field(None, description="User ID")


class TaskExtractionResponse(BaseModel):
    """Response with extracted task information."""
    
    summary: str = Field(..., description="Brief task summary (5-7 words)")
    description: str = Field(..., description="Detailed task description")
    assignee: str = Field(default="сотрудник", description="Task assignee")
    priority: str = Field(default="medium", description="Task priority")
    category_id: Optional[int] = None
    confidence: float = Field(..., description="Extraction confidence (0-1)")

