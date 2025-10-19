"""Schemas for classification corrections and examples."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ClassificationCorrectionCreate(BaseModel):
    """Schema for creating a classification correction."""
    
    user_message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1, max_length=100)
    user_id: int
    
    # Predicted (incorrect)
    predicted_category: Optional[str] = None
    predicted_intent: Optional[str] = None
    predicted_priority: Optional[str] = None
    
    # Corrected (correct)
    correct_category: Optional[str] = None
    correct_intent: Optional[str] = None
    correct_priority: Optional[str] = None
    
    notes: Optional[str] = None


class ClassificationCorrectionResponse(BaseModel):
    """Schema for classification correction response."""
    
    id: int
    user_message: str
    
    predicted_category: Optional[str]
    predicted_intent: Optional[str]
    predicted_priority: Optional[str]
    
    correct_category: Optional[str]
    correct_intent: Optional[str]
    correct_priority: Optional[str]
    
    session_id: str
    user_id: int
    correction_type: str
    is_active: bool
    notes: Optional[str]
    
    times_used: int
    last_used_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClassificationExampleCreate(BaseModel):
    """Schema for creating a classification example."""
    
    example_text: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(..., min_length=1, max_length=50)
    intent: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)
    reasoning: Optional[str] = None
    source: Optional[str] = None
    priority_order: int = Field(default=0)


class ClassificationExampleUpdate(BaseModel):
    """Schema for updating a classification example."""
    
    example_text: Optional[str] = Field(None, min_length=1, max_length=2000)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    intent: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=20)
    reasoning: Optional[str] = None
    is_active: Optional[bool] = None
    priority_order: Optional[int] = None


class ClassificationExampleResponse(BaseModel):
    """Schema for classification example response."""
    
    id: int
    example_text: str
    category: str
    intent: Optional[str]
    priority: Optional[str]
    reasoning: Optional[str]
    
    example_type: str
    source: Optional[str]
    is_active: bool
    priority_order: int
    
    times_used: int
    last_used_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClassificationCorrectionListResponse(BaseModel):
    """Response for list of corrections."""
    
    corrections: list[ClassificationCorrectionResponse]
    total: int


class ClassificationExampleListResponse(BaseModel):
    """Response for list of examples."""
    
    examples: list[ClassificationExampleResponse]
    total: int

