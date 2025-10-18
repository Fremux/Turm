from sqlalchemy import String, TIMESTAMP
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime
from typing import List
from sqlalchemy.dialects.postgresql import JSONB
from models.base import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    surname: Mapped[str] = mapped_column(String)
    patronymic: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String)
    organization: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    sector: Mapped[str] = mapped_column(String)
    tags: Mapped[List[str]] = mapped_column(JSONB, nullable=False, server_default="{}")
    birth_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(String)
