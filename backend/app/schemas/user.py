from pydantic import BaseModel
from datetime import datetime
from typing import List
from schemas.enum import UnitType
from dataclasses import dataclass


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
    command: str
    patronymic: str | None
    email: str
    organization: str
    role: str
    role_id: str
    tags: List[str]
    birth_date: datetime
    description: str


class CreateUserResponse(BaseModel):
    user_id: int


class CreateUserRequest(BaseModel):
    name: str
    surname: str
    patronymic: str | None
    email: str
    organization: str
    command: str
    role_id: str
    tags: List[str]
    birth_date: datetime
    description: str | None = "Описание пользователя пока не заполнено"


class UpdateUserRequest(BaseModel):
    name: str
    surname: str
    patronymic: str | None
    email: str
    organization: str
    command: str
    role: str
    role_id: str
    sector: str
    tags: List[str]
    birth_date: datetime
    description: str


class GetAllUserResponse(BaseModel):
    id: int
    name: str
    surname: str
    patronymic: str
    email: str
    organization: str
    role: str
    role_id: str
    command: str
    tags: List[str]
    birth_date: datetime
    description: str


@dataclass
class GetUserDTO:
    id: int
    name: str
    surname: str
    patronymic: str
    email: str
    organization: str
    role: str
    role_id: str
    command: str
    tags: List[str]
    birth_date: datetime
    description: str
