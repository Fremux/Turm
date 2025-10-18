from sqlalchemy import select, update, insert, delete, literal
from models.user import UserInfo
from models.organizations import OrgNode
from core.db import AsyncSession
from typing import List
from datetime import datetime
from schemas.user import GetUserDTO


async def create_user(name: str,
                      surname: str,
                      patronymic: str | None,
                      email: str,
                      command: str,
                      organization: str,
                      role_id: str,
                      tags: List[str],
                      birth_date: datetime,
                      description: str,
                      db: AsyncSession) -> int:
    stmt = (
        insert(UserInfo)
        .values(
            name=name,
            surname=surname,
            patronymic=patronymic,
            organization=organization,
            email=email,
            role_id=role_id,
            command=command,
            tags=tags,
            birth_date=birth_date,
            description=description,
        )
        .returning(UserInfo.id)
    )

    result = await db.execute(stmt)
    user_id = result.scalar()
    await db.commit()

    return user_id


async def get_user_by_id(user_id: int,
                         db: AsyncSession):
    """Get full user info by user id"""
    stmt = select(UserInfo, OrgNode).where(UserInfo.id == literal(user_id)).join(OrgNode, OrgNode.id == UserInfo.role_id)
    res = await db.execute(stmt)

    return res.fetchone()


async def get_all_user_with_filtration(db: AsyncSession,
                                       limit: int,
                                       offset: int,
                                       command: str | None = None,
                                       role_title: str | None = None) -> List[GetUserDTO]:
    """Get all users with filtration"""
    stmt = select(UserInfo, OrgNode).join(OrgNode, UserInfo.role_id == OrgNode.id).limit(limit).offset(offset)

    if role_title is not None:
        stmt = stmt.where(OrgNode.id == literal(role_title))
    if command is not None:
        stmt = stmt.where(UserInfo.command == literal(command))

    result = await db.execute(stmt)
    result = result.all()

    return [GetUserDTO(id=r[0].id,
                       name=r[0].name,
                       surname=r[0].surname,
                       patronymic=r[0].patronymic,
                       email=r[0].email,
                       organization=r[0].organization,
                       role=r[1].title,
                       role_id=r[1].id,
                       command=r[0].command,
                       tags=r[0].tags,
                       birth_date=r[0].birth_date,
                       description=r[0].description,) for r in result]


async def update_user(user_id: int | None,
                      name: str | None,
                      surname: str | None,
                      patronymic: str | None,
                      email: str | None,
                      organization: str | None,
                      role: str | None,
                      sector: str | None,
                      tags: List[str] | None,
                      birth_date: datetime | None,
                      description: str | None,
                      db: AsyncSession) -> None:
    """Update user"""
    stmt = update(UserInfo).where(UserInfo.id == literal(user_id))

    if name is not None:
        stmt = stmt.values(name=name)
    if surname is not None:
        stmt = stmt.values(surname=surname)
    if patronymic is not None:
        stmt = stmt.values(patronymic=patronymic)
    if email is not None:
        stmt = stmt.values(email=email)
    if organization is not None:
        stmt = stmt.values(organization=organization)
    if role is not None:
        stmt = stmt.values(role=role)
    if sector is not None:
        stmt = stmt.values(sector=sector)
    if tags is not None:
        stmt = stmt.values(tags=tags)
    if birth_date is not None:
        stmt = stmt.values(birth_date=birth_date)
    if description is not None:
        stmt = stmt.values(description=description)

    await db.execute(stmt)
    await db.commit()


async def delete_user(user_id: int,
                      db: AsyncSession):
    """Delete user by its id"""
    stmt = delete(UserInfo).where(UserInfo.id == literal(user_id))
    await db.execute(stmt)
    await db.commit()
