"""Schemas for category and intent management."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Category Schemas
class CategoryCreate(BaseModel):
    """Schema for creating a new category."""
    
    name: str = Field(..., description="Internal name (e.g., 'hr', 'it')", min_length=2, max_length=50)
    display_name: str = Field(..., description="Display name (e.g., 'Human Resources')", min_length=2, max_length=100)
    description: str = Field(..., description="Category description", max_length=500)
    
    # Prompt customization fields
    about_text: Optional[str] = Field(None, description="О чём: описание того, что входит в эту категорию", max_length=2000)
    common_intents: Optional[str] = Field(None, description="Частые интенты: что чаще всего хотят пользователи", max_length=2000)
    key_markers: Optional[str] = Field(None, description="Ключевые маркеры: слова и фразы для определения категории", max_length=2000)
    example_queries: Optional[str] = Field(None, description="Примеры запросов: примеры сообщений пользователей", max_length=2000)
    border_cases: Optional[str] = Field(None, description="Пограничные случаи: как отличать от других категорий", max_length=2000)
    
    color: Optional[str] = Field(None, description="UI color (e.g., '#3b82f6')", max_length=20)
    icon: Optional[str] = Field(None, description="UI icon name", max_length=50)
    
    # Embedding settings
    embedding_model: Optional[str] = Field("bge-m3", description="Embedding model to use", max_length=100)
    embedding_dimension: Optional[int] = Field(1024, description="Embedding vector dimension")
    
    create_collection: bool = Field(default=True, description="Auto-create vector collection")


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    # Prompt customization fields
    about_text: Optional[str] = Field(None, max_length=2000)
    common_intents: Optional[str] = Field(None, max_length=2000)
    key_markers: Optional[str] = Field(None, max_length=2000)
    example_queries: Optional[str] = Field(None, max_length=2000)
    border_cases: Optional[str] = Field(None, max_length=2000)
    
    # Embedding settings
    embedding_model: Optional[str] = Field(None, max_length=100)
    embedding_dimension: Optional[int] = None
    
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Schema for category response."""
    
    id: int
    name: str
    display_name: str
    description: str
    
    # Prompt customization fields
    about_text: Optional[str] = None
    common_intents: Optional[str] = None
    key_markers: Optional[str] = None
    example_queries: Optional[str] = None
    border_cases: Optional[str] = None
    
    collection_name: str
    collection_created: bool
    
    # Embedding settings
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    
    is_active: bool
    color: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime
    
    # Stats
    intents_count: int = Field(default=0, description="Number of associated intents")
    documents_count: int = Field(default=0, description="Number of documents in collection")


# Intent Schemas
class IntentCreate(BaseModel):
    """Schema for creating a new intent."""
    
    name: str = Field(..., description="Internal name (e.g., 'ask_question')", min_length=2, max_length=50)
    display_name: str = Field(..., description="Display name (e.g., 'Ask a Question')", min_length=2, max_length=100)
    description: str = Field(..., description="Intent description", max_length=500)
    examples: list[str] = Field(default=[], description="Example phrases for this intent")
    category_id: Optional[int] = Field(None, description="Associated category ID")
    priority: Optional[str] = Field("normal", description="Priority level")


class IntentUpdate(BaseModel):
    """Schema for updating an intent."""
    
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    examples: Optional[list[str]] = None
    category_id: Optional[int] = None
    priority: Optional[str] = None
    is_active: Optional[bool] = None


class IntentResponse(BaseModel):
    """Schema for intent response."""
    
    id: int
    name: str
    display_name: str
    description: str
    examples: list[str]
    category_id: Optional[int]
    category_name: Optional[str] = None
    priority: Optional[str]
    is_active: bool
    created_at: datetime


# List responses
class CategoriesListResponse(BaseModel):
    """Response for list of categories."""
    
    categories: list[CategoryResponse]
    total: int


class IntentsListResponse(BaseModel):
    """Response for list of intents."""
    
    intents: list[IntentResponse]
    total: int

