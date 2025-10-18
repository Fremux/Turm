from sqlalchemy import select, update, insert, delete, literal
from models.user import User
from core.db import AsyncSession
from typing import List
from datetime import datetime


async def create_user(name: str,
                      surname: str,
                      patronymic: str | None,
                      email: str,
                      organization: str,
                      role: str,
                      sector: str,
                      tags: List[str],
                      birth_date: datetime,
                      description: str,
                      db: AsyncSession) -> int:
    stmt = (
        insert(User)
        .values(
            name=name,
            surname=surname,
            patronymic=patronymic,
            email=email,
            organization=organization,
            role=role,
            sector=sector,
            tags=tags,
            birth_date=birth_date,
            description=description,
        )
        .returning(User.id)
    )
    result = await db.execute(stmt)
    user_id = result.scalar()
    await db.commit()

    return user_id


async def get_user_by_id(user_id: int,
                         db: AsyncSession) -> User | None:
    stmt = select(User).where(User.id == literal(user_id))
    res = await db.execute(stmt)

    return res.scalar_one_or_none()


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
    stmt = update(User).where(User.id == literal(user_id))

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
    stmt = delete(User).where(User.id == literal(user_id))
    await db.execute(stmt)
    await db.commit()
