from models.base import Base
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from schemas.enum import UnitType


class OrgNode(Base):
    __tablename__ = "org_nodes"

    id: Mapped[str] = mapped_column(String,
                                    primary_key=True)
    title: Mapped[str] = mapped_column(Text,
                                       nullable=False)
    position: Mapped[Optional[str]] = mapped_column(Text)
    unit_type: Mapped[UnitType] = mapped_column(Enum(UnitType),
                                                nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("org_nodes.id", ondelete="SET NULL")
    )

    # Relationships
    children: Mapped[list["OrgNode"]] = relationship(cascade="all, delete",
                                                     back_populates="parent")
    parent: Mapped[Optional["OrgNode"]] = relationship(remote_side=[id],
                                                       back_populates="children")
