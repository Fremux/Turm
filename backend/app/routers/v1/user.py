from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.sql import crud

from core.db import get_async_database, AsyncSession
from schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    GetUserResponse,
    GetAllUserResponse,
    UpdateUserRequest
)
from typing import List
import crud.user as user_crud


router = APIRouter()


@router.get("/{user_id}",
            response_model=GetUserResponse)
async def get_user(user_id: int,
                   db: AsyncSession = Depends(get_async_database)) -> GetUserResponse:
    """Get user by its id"""
    user = await user_crud.get_user_by_id(user_id=user_id,
                                          db=db)

    return GetUserResponse(id=user.id,
                           name=user.name,
                           surname=user.surname,
                           patronymic=user.patronymic,
                           email=user.email,
                           organization=user.organization,
                           role=user.role,
                           sector=user.sector,
                           tags=user.tags,
                           birth_date=user.birth_date,
                           description=user.description)


@router.get("/all/",
            response_model=List[GetAllUserResponse])
async def get_all_users(limit: int = 20,
                        offset: int = 0,
                        db: AsyncSession = Depends(get_async_database)) -> List[GetAllUserResponse]:
    pass


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
                                              role=user_data.role,
                                              sector=user_data.patronymic,
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
