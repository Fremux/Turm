"""Task model for task management system."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship, Column
from sqlalchemy import func, DateTime
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category


class TaskStatus:
    """Task status constants."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(BaseModel, table=True):
    """Model for tasks created from user requests.
    
    Tasks are created when user asks for something to be done
    (fix a lamp, create a document, etc.)
    """
    
    __tablename__ = "tasks"
    
    id: int = Field(default=None, primary_key=True)
    
    # Task info
    summary: str = Field(max_length=200, description="Brief task description (5-7 words)")
    description: str = Field(max_length=2000, description="Detailed task description")
    
    # Assignment
    assignee: str = Field(default="сотрудник", max_length=100, description="Who should complete the task")
    
    # Task metadata
    status: str = Field(default=TaskStatus.PENDING, max_length=20, index=True)
    priority: str = Field(default="medium", max_length=20)  # low, medium, high, urgent
    
    # Relations
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    category: Optional["Category"] = Relationship()
    
    # Creator (who requested the task) - just store ID without foreign key
    created_by: Optional[int] = Field(default=None)
    
    # Original message that created the task
    original_message: Optional[str] = Field(default=None, max_length=1000)
    
    # Completion
    completed_at: Optional[datetime] = Field(default=None)
    completed_by: Optional[str] = Field(default=None, max_length=100)
    
    # Notes
    notes: Optional[str] = Field(default=None, max_length=2000)
    
    # Timestamps
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )


# Avoid circular imports
from app.models.user import User
from app.models.category import Category

