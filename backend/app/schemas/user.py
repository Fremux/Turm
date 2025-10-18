from pydantic import BaseModel
from datetime import datetime
from typing import List
from schemas.enum import UnitType


class OrgNodeInfo(BaseModel):
    id: str
    title: str
    position: str | None
    unit_type: UnitType
    parent_id: str | None


class GetUserResponse(BaseModel):
    id: int
    name: str
    surname: str
    patronymic: str | None
    email: str
    organization: str
    role: str
    sector: str
    tags: List[str]
    birth_date: datetime
    description: str
    org_node: OrgNodeInfo


class CreateUserResponse(BaseModel):
    user_id: int


class CreateUserRequest(BaseModel):
    name: str
    surname: str
    patronymic: str | None
    email: str
    organization: str
    role: str
    sector: str
    tags: List[str]
    birth_date: datetime
    description: str | None = "Описание пользователя пока не заполнено"


class UpdateUserRequest(BaseModel):
    name: str
    surname: str
    patronymic: str | None
    email: str
    organization: str
    role: str
    sector: str
    tags: List[str]
    birth_date: datetime
    description: str


class GetAllUserResponse(BaseModel):
    id: int
    name: str
    surname: str
    email: str
    organization: str
    role: str
    sector: str
    tags: List[str]
    birth_date: datetime
    description: str
