"""Category and Intent models for dynamic classification."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship, Column, JSON
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Category(BaseModel, table=True):
    """Model for classification categories.
    
    Categories define the main domains (HR, IT, Finance, etc.)
    Each category can have its own vector collection for RAG.
    """
    
    __tablename__ = "categories"
    
    id: int = Field(default=None, primary_key=True)
    
    # Category info
    name: str = Field(max_length=50, unique=True, index=True)
    display_name: str = Field(max_length=100)
    description: str = Field(max_length=500)
    
    # Prompt customization fields (for classifier)
    about_text: Optional[str] = Field(default=None, max_length=2000)  # "О чём" - описание того, что входит в эту категорию
    common_intents: Optional[str] = Field(default=None, max_length=2000)  # "Частые интенты" - что чаще всего хотят пользователи
    key_markers: Optional[str] = Field(default=None, max_length=2000)  # "Ключевые маркеры" - слова и фразы для определения категории
    example_queries: Optional[str] = Field(default=None, max_length=2000)  # "Примеры запросов" - примеры сообщений пользователей
    border_cases: Optional[str] = Field(default=None, max_length=2000)  # "Пограничные случаи" - как отличать от других категорий
    
    # Collection settings
    collection_name: str = Field(max_length=50, unique=True, index=True)
    collection_created: bool = Field(default=False)
    
    # Embedding settings for this category's collection
    embedding_model: Optional[str] = Field(default="bge-m3", max_length=100)
    embedding_dimension: Optional[int] = Field(default=1024)
    
    # Status
    is_active: bool = Field(default=True, index=True)
    
    # Metadata
    color: Optional[str] = Field(default=None, max_length=20)  # For UI
    icon: Optional[str] = Field(default=None, max_length=50)   # For UI
    
    # Relationships
    intents: list["Intent"] = Relationship(back_populates="category")
    
    # Audit
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")
    creator: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Category.created_by]",
            "lazy": "selectin"
        }
    )


class Intent(BaseModel, table=True):
    """Model for user intents.
    
    Intents define what users want to do (ask_question, report_issue, etc.)
    """
    
    __tablename__ = "intents"
    
    id: int = Field(default=None, primary_key=True)
    
    # Intent info
    name: str = Field(max_length=50, unique=True, index=True)
    display_name: str = Field(max_length=100)
    description: str = Field(max_length=500)
    
    # Examples for classification
    examples: list[str] = Field(default=[], sa_column=Column(JSON))
    
    # Associated category (optional)
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    category: Optional["Category"] = Relationship(back_populates="intents")
    
    # Status
    is_active: bool = Field(default=True, index=True)
    
    # Metadata
    priority: Optional[str] = Field(default="normal", max_length=20)  # low, normal, high, urgent
    
    # Audit
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")
    creator: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Intent.created_by]",
            "lazy": "selectin"
        }
    )


# Avoid circular imports
from app.models.user import User

