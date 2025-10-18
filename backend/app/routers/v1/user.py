from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from core.db import get_async_database, AsyncSession
from schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    GetUserResponse,
    GetAllUserResponse,
    UpdateUserRequest
)

import crud.user as user_crud


router = APIRouter()


@router.get("/{user_id}",
            response_model=GetUserResponse)
async def get_user(user_id: int,
                   db: AsyncSession = Depends(get_async_database)) -> GetUserResponse:
    """Get user by its id"""
    user = await user_crud.get_user_by_id(user_id=user_id,
                                          db=db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User does not exists!")

    return GetUserResponse(id=user[0].id,
                           name=user[0].name,
                           surname=user[0].surname,
                           patronymic=user[0].patronymic,
                           email=user[0].email,
                           organization=user[0].organization,
                           role=user[1].title,
                           role_id=user[1].id,
                           command=user[0].command,
                           tags=user[0].tags,
                           birth_date=user[0].birth_date,
                           description=user[0].description)


@router.get("/all/",
            response_model=List[GetAllUserResponse])
async def get_all_users(command: str | None = None,
                        role: str | None = None,
                        limit: int = 20,
                        offset: int = 0,
                        db: AsyncSession = Depends(get_async_database)) -> List[GetAllUserResponse]:
    """Get all users with filtration"""
    users = await user_crud.get_all_user_with_filtration(limit=limit,
                                                         offset=offset,
                                                         db=db,
                                                         command=command,
                                                         role_title=role)

    return [GetAllUserResponse(id=user.id,
                               name=user.name,
                               surname=user.surname,
                               patronymic=user.patronymic,
                               email=user.email,
                               organization=user.organization,
                               role=user.role,
                               role_id=user.role_id,
                               command=user.command,
                               tags=user.tags,
                               birth_date=user.birth_date,
                               description=user.description,) for user in users]


@router.post("",
             response_model=CreateUserResponse)
async def create_user(user_data: CreateUserRequest,
                      db: AsyncSession = Depends(get_async_database)) -> CreateUserResponse:
    """Create user"""
    new_user_id = await user_crud.create_user(name=user_data.name,
                                              surname=user_data.surname,
                                              patronymic=user_data.patronymic,
                                              email=user_data.email,
                                              organization=user_data.organization,
                                              role_id=user_data.role_id,
                                              command=user_data.command,
                                              tags=user_data.tags,
                                              birth_date=user_data.birth_date,
                                              description=user_data.description,
                                              db=db)

    return CreateUserResponse(user_id=new_user_id)


@router.delete("/{user_id}",
               status_code=200)
async def delete_user(user_id: int,
                      db: AsyncSession = Depends(get_async_database)) -> None:
    """Delete user by its id"""
    user = await user_crud.get_user_by_id(user_id=user_id,
                                          db=db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found!")

    await user_crud.delete_user(user_id=user_id,
                                db=db)


@router.patch("/{user_id}",
              status_code=200)
async def update_user(user_id: str,
                      update_data: UpdateUserRequest,
                      db: AsyncSession = Depends(get_async_database)) -> None:
    pass


@router.get("/me",
            response_model=GetUserResponse)
async def get_me(user_id: int,
                 db: AsyncSession = Depends(get_async_database)) -> GetUserResponse:
    pass
