from enum import StrEnum


class SubtypeType(StrEnum):
    ACTION = 'action'
    ENTITY = 'entity'
    SYSTEM = 'system'


class UnitType(StrEnum):
    CORPORATION = 'corporation'
    BOARD = 'board'
    ROLE = 'role'
    BLOCK = 'block'
    DEPARTMENT = 'department'
    DIRECTORATE = 'directorate'
    DIVISION = 'division'
    OFFICE = 'office'
    TEAM = 'team'
    POSITION = 'position'
