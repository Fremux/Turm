from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB

from models.base import BaseModel  # ваш BaseModel с created_at


class UserInfo(BaseModel, table=True):
    __tablename__ = "user_info"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, nullable=False))
    surname: str = Field(sa_column=Column(String, nullable=False))
    patronymic: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True),
    )
    email: str = Field(sa_column=Column(String, nullable=False))
    command: str = Field(sa_column=Column(String, nullable=False))
    role_id: str = Field(
        sa_column=Column(String, nullable=False),
        foreign_key="org_nodes.id",
    )
    tags: List[str] = Field(
        sa_column=Column(
            JSONB,
            nullable=False,
            server_default=text("'{}'::jsonb"),
        )
    )
    birth_date: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    description: str = Field(sa_column=Column(String, nullable=False))
    organization: str = Field(sa_column=Column(String, nullable=False))
    user_id: int = Field(
        foreign_key="user.id",
        index=True,
        nullable=False,
    )
