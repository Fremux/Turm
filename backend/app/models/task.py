from sqlalchemy import Text, Integer, CheckConstraint, String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from models.base import Base
from models.organizations import OrgNode
from schemas.enum import SubtypeType


class TaskCategory(Base):
    __tablename__ = "task_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    task_items: Mapped[list["TaskItem"]] = relationship(
        back_populates="category", cascade="all, delete"
    )


class TaskItem(Base):
    __tablename__ = 'task_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('task_categories.id', ondelete='CASCADE'),
        nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    subtype: Mapped[SubtypeType] = mapped_column(Enum(SubtypeType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    category: Mapped['TaskCategory'] = relationship(back_populates='task_items')
    routing: Mapped['TaskRouting'] = relationship(back_populates='task_item')


class TaskRouting(Base):
    __tablename__ = 'task_routing'

    task_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('task_items.id', ondelete='CASCADE'),
        primary_key=True
    )
    handled_by_id: Mapped[str] = mapped_column(
        String,
        ForeignKey('org_nodes.id', ondelete='RESTRICT'),
        nullable=False
    )
    escalate_to_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey('org_nodes.id', ondelete='SET NULL')
    )
    coord_with_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey('org_nodes.id', ondelete='SET NULL')
    )

    # Relationships
    task_item: Mapped['TaskItem'] = relationship(back_populates='routing')
    handled_by: Mapped['OrgNode'] = relationship(
        foreign_keys=[handled_by_id],
        primaryjoin="TaskRouting.handled_by_id == OrgNode.id"
    )
    escalate_to: Mapped[Optional['OrgNode']] = relationship(
        foreign_keys=[escalate_to_id],
        primaryjoin="TaskRouting.escalate_to_id == OrgNode.id"
    )
    coord_with: Mapped[Optional['OrgNode']] = relationship(
        foreign_keys=[coord_with_id],
        primaryjoin="TaskRouting.coord_with_id == OrgNode.id"
    )
