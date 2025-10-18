"""Entity model for storing extracted user information."""

from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Field, Relationship, Column, String
from models.base import BaseModel

if TYPE_CHECKING:
    from models.user import User


class UserEntity(BaseModel, table=True):
    """Model for storing extracted entities about users.

    Attributes:
        id: The primary key
        user_id: Foreign key to the user
        session_id: The session where this entity was extracted
        entity_type: Type of entity (name, preference, usage, personal_info, etc.)
        entity_value: The actual value of the entity
        context: Additional context about where/how this was mentioned
        confidence: Confidence score of extraction (0-1)
        created_at: When the entity was extracted
    """

    __tablename__ = "user_entity"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    session_id: str = Field(index=True)
    entity_type: str = Field(max_length=100, index=True)
    entity_value: str = Field(max_length=500)
    context: Optional[str] = Field(default=None, max_length=1000)
    confidence: float = Field(default=1.0)

    # Relationship
    user: Optional["User"] = Relationship(back_populates="entities")


# Avoid circular imports
from models.user import User  # noqa: E402
