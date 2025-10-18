from sqlalchemy.orm import declarative_base
from sqlmodel import Field, SQLModel
from datetime import datetime, UTC


class BaseModel(SQLModel):
    """Base model with common fields."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


Base = declarative_base()
