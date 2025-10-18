from fastapi import APIRouter, Depends
from core.db import AsyncSession, get_async_database
from typing import List
import crud.organizations as organizations_crud
from schemas.organizations import GetAllUnitTypesResponse, GetAllNodesResponse
from schemas.enum import UnitType
import logging


router = APIRouter()


@router.get('/all', response_model=List[GetAllNodesResponse])
async def get_all_organizations_nodes(unit_type: UnitType | None = None,
                                      db: AsyncSession = Depends(get_async_database)) -> List[GetAllNodesResponse]:
    """Get all organizations nodes with filter by unit type"""

    org_nodes = await organizations_crud.get_org_nodes(unit_type=unit_type,
                                                       db=db)

    return [GetAllNodesResponse(id=org_node.id,
                                title=org_node.title,
                                position=org_node.position,
                                unit_type=org_node.unit_type,
                                parent_id=org_node.parent_id) for org_node in org_nodes]


@router.get('/unit_types',
            response_model=List[GetAllUnitTypesResponse])
async def get_all_unit_types_nodes() -> List[GetAllUnitTypesResponse]:
    """Get all unit types in available in system"""
    all_unit_types = ['corporation',
                      'board',
                      'role',
                      'block',
                      'department',
                      'directorate',
                      'division',
                      'office',
                      'team',
                      'position']

    return [GetAllUnitTypesResponse(name=unit_type) for unit_type in all_unit_types]
