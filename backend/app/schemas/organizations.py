from pydantic import BaseModel
from schemas.enum import UnitType
from dataclasses import dataclass


class GetAllNodesResponse(BaseModel):
    id: str
    title: str
    position: str | None
    unit_type: UnitType
    parent_id: str | None


@dataclass
class GetAllNodesDTO:
    id: str
    title: str
    position: str | None
    unit_type: UnitType
    parent_id: str | None


class GetAllUnitTypesResponse(BaseModel):
    name: str
