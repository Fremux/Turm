"""Models for classification corrections and fine-tuning examples."""

from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from app.models.base import BaseModel


class ClassificationCorrection(BaseModel, table=True):
    """Stores user corrections to classifications for model improvement.
    
    When a user corrects a classification, we store it as an example
    to improve future classifications.
    """
    
    __tablename__ = "classification_corrections"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Original message and classification
    user_message: str = Field(
        index=True,
        description="The original user message that was classified"
    )
    
    # Incorrect classification (what the model predicted)
    predicted_category: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Category predicted by the model"
    )
    predicted_intent: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Intent predicted by the model"
    )
    predicted_priority: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Priority predicted by the model"
    )
    
    # Correct classification (what the user corrected to)
    correct_category: Optional[str] = Field(
        default=None,
        max_length=50,
        index=True,
        description="Corrected category"
    )
    correct_intent: Optional[str] = Field(
        default=None,
        max_length=50,
        index=True,
        description="Corrected intent"
    )
    correct_priority: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Corrected priority"
    )
    
    # Context
    session_id: str = Field(
        max_length=100,
        index=True,
        description="Session where the correction was made"
    )
    user_id: int = Field(
        index=True,
        description="User who made the correction"
    )
    
    # Metadata
    correction_type: str = Field(
        default="manual",
        max_length=20,
        description="Type: manual, automatic, imported"
    )
    is_active: bool = Field(
        default=True,
        index=True,
        description="Whether this example should be used for training"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes about the correction"
    )
    
    # Usage tracking
    times_used: int = Field(
        default=0,
        description="How many times this example was used in classification"
    )
    last_used_at: Optional[datetime] = Field(
        default=None,
        description="When this example was last used"
    )


class ClassificationExample(BaseModel, table=True):
    """Curated examples for few-shot learning in classification.
    
    These are high-quality examples added by admins to guide the classifier.
    """
    
    __tablename__ = "classification_examples"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Example data
    example_text: str = Field(
        description="Example user message"
    )
    
    # Classification
    category: str = Field(
        max_length=50,
        index=True,
        description="Category for this example"
    )
    intent: Optional[str] = Field(
        default=None,
        max_length=50,
        index=True,
        description="Intent for this example"
    )
    priority: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Priority for this example"
    )
    
    # Context
    reasoning: Optional[str] = Field(
        default=None,
        description="Explanation of why this classification is correct"
    )
    
    # Metadata
    example_type: str = Field(
        default="manual",
        max_length=20,
        description="Type: manual, imported, from_correction"
    )
    source: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Source of the example (user, import, etc)"
    )
    is_active: bool = Field(
        default=True,
        index=True,
        description="Whether to use this example in classification"
    )
    priority_order: int = Field(
        default=0,
        description="Order priority (higher = more important)"
    )
    
    # Usage tracking
    times_used: int = Field(
        default=0,
        description="How many times used in classification"
    )
    last_used_at: Optional[datetime] = Field(
        default=None,
        description="Last time this example was used"
    )

