from sqlalchemy import select, literal
from models.organizations import OrgNode
from core.db import AsyncSession
from typing import List
from schemas.enum import UnitType
from schemas.organizations import GetAllNodesDTO


async def get_org_nodes(unit_type: UnitType | None,
                        db: AsyncSession) -> List[GetAllNodesDTO]:
    """Get all org nodes with filtration by unit type."""
    stmt = select(OrgNode)

    if unit_type is not None:
        stmt = stmt.where(OrgNode.unit_type == literal(unit_type))

    result = await db.execute(stmt)
    org_nodes = result.all()

    return [GetAllNodesDTO(id=org_node[0].id,
                           title=org_node[0].title,
                           position=org_node[0].position,
                           unit_type=org_node[0].unit_type,
                           parent_id=org_node[0].parent_id) for org_node in org_nodes]
