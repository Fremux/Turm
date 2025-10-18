# models/org_node.py
from __future__ import annotations

from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Text, Enum as SAEnum, ForeignKey
from models.base import BaseModel
from schemas.enum import UnitType


class OrgNode(BaseModel, table=True):
    __tablename__ = "org_nodes"

    id: str = Field(primary_key=True, sa_column=Column(String))
    title: str = Field(sa_column=Column(Text, nullable=False))
    position: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    # Enum через SQLAlchemy-колонку
    unit_type: UnitType = Field(sa_column=Column(SAEnum(UnitType), nullable=False))

    # самоссылка с ON DELETE SET NULL
    parent_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            ForeignKey("org_nodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # --- relationships ---
    children: List["OrgNode"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={
            "cascade": "all, delete",
            "passive_deletes": True,
        },
    )
    parent: Optional["OrgNode"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "OrgNode.id"},
    )
