from fastapi import APIRouter
from routers.v1.user import router as user_router
from routers.v1.organizations import router as organization_router


router = APIRouter(prefix="/v1")
router.include_router(user_router, prefix="/user", tags=["User"])
