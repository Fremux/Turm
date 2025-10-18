from sqlalchemy import String, TIMESTAMP, ForeignKey, Float
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime
from typing import List, Optional
from sqlalchemy.dialects.postgresql import JSONB
from models.base import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    surname: Mapped[str] = mapped_column(String)
    patronymic: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String)
    command: Mapped[str] = mapped_column(String)
    role_id: Mapped[str] = mapped_column(String, ForeignKey("org_nodes.id"))
    tags: Mapped[List[str]] = mapped_column(JSONB, nullable=False, server_default="{}")
    birth_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(String)
    organization: Mapped[str] = mapped_column(String)
    user_id: Mapped[int] = mapped_column(foreign_key="user.id", index=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    entity_type: Mapped[str] = mapped_column(String, index=True)
    entity_value: Mapped[str] = mapped_column(String(500))
    context: Mapped[Optional[str]] = mapped_column(String(1000), default=None, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
