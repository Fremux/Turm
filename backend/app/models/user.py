"""This file contains the user model for the application."""

from typing import (
    TYPE_CHECKING,
    List,
)

import bcrypt
from sqlmodel import (
    Field,
    Relationship,
)

from models.base import BaseModel

if TYPE_CHECKING:
    from models.session import Session
    from models.entity import UserEntity
    from models.agent_analysis import AgentAnalysis


class User(BaseModel, table=True):
    """User model for storing user accounts.

    Attributes:
        id: The primary key
        username: User's username (unique)
        hashed_password: Bcrypt hashed password
        created_at: When the user was created
        sessions: Relationship to user's chat sessions
        entities: Relationship to extracted user entities
        agent_analyses: Relationship to agent analysis results
    """

    id: int = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    sessions: List["Session"] = Relationship(back_populates="user")
    entities: List["UserEntity"] = Relationship(back_populates="user")
    agent_analyses: List["AgentAnalysis"] = Relationship(back_populates="user")

    def verify_password(self, password: str) -> bool:
        """Verify if the provided password matches the hash."""
        return bcrypt.checkpw(password.encode("utf-8"), self.hashed_password.encode("utf-8"))

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# Avoid circular imports
from models.session import Session  # noqa: E402
from models.entity import UserEntity  # noqa: E402
from models.agent_analysis import AgentAnalysis  # noqa: E402