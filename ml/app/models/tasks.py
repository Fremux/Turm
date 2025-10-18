# models/tasks.py
from __future__ import annotations

from typing import List, Optional

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Integer, String, Text, Enum as SAEnum, ForeignKey
from models.base import BaseModel
from schemas.enum import SubtypeType
from models.organizations import OrgNode


class TaskCategory(BaseModel, table=True):
    __tablename__ = "task_categories"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(sa_column=Column(Text, unique=True, nullable=False))
    name: str = Field(sa_column=Column(Text, nullable=False))

    # Relationships
    task_items: List["TaskItem"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={
            "cascade": "all, delete",
            "passive_deletes": True,
        },
    )


class TaskItem(BaseModel, table=True):
    __tablename__ = "task_items"

    id: int | None = Field(default=None, primary_key=True)

    category_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("task_categories.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    name: str = Field(sa_column=Column(Text, nullable=False))
    subtype: SubtypeType = Field(sa_column=Column(SAEnum(SubtypeType), nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    category: "TaskCategory" = Relationship(back_populates="task_items")

    routing: Optional["TaskRouting"] = Relationship(
        back_populates="task_item",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )


class TaskRouting(BaseModel, table=True):
    __tablename__ = "task_routing"

    task_item_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("task_items.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )

    handled_by_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("org_nodes.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    escalate_to_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            ForeignKey("org_nodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    coord_with_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String,
            ForeignKey("org_nodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Relationships
    task_item: "TaskItem" = Relationship(back_populates="routing")

    handled_by: "OrgNode" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[TaskRouting.handled_by_id]",
            "primaryjoin": "TaskRouting.handled_by_id == OrgNode.id",
        }
    )
    escalate_to: Optional["OrgNode"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[TaskRouting.escalate_to_id]",
            "primaryjoin": "TaskRouting.escalate_to_id == OrgNode.id",
        }
    )
    coord_with: Optional["OrgNode"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[TaskRouting.coord_with_id]",
            "primaryjoin": "TaskRouting.coord_with_id == OrgNode.id",
        }
    )
