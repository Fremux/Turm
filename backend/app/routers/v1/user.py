from fastapi import APIRouter, Depends, HTTPException
from core.db import get_async_database, AsyncSession


router = APIRouter()


@router.get("/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_async_database)):
    pass


@router.get("/all/")
async def get_all_users(
    limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_async_database)
):
    pass


@router.post("")
async def create_user(db: AsyncSession = Depends(get_async_database)):
    pass


@router.delete("/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_async_database)):
    pass


@router.patch("/{user_id}")
async def update_user(user_id: str, db: AsyncSession = Depends(get_async_database)):
    pass


@router.get("/me")
async def get_me(user_id: int, db: AsyncSession = Depends(get_async_database)):
    pass
