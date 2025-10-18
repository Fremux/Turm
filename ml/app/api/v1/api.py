"""API v1 router configuration.

This module sets up the main API router and includes all sub-routers for different
endpoints like authentication and chatbot functionality.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chatbot import router as chatbot_router
from app.api.v1.classifier import router as classifier_router
from app.api.v1.agent import router as agent_router
from app.api.v1.documents import router as documents_router
from app.api.v1.entities import router as entities_router
from app.api.v1.analyses import router as analyses_router
from app.core.logging import logger

api_router = APIRouter()

# Include routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["chatbot"])
api_router.include_router(classifier_router, prefix="/classifier", tags=["classifier"])
api_router.include_router(agent_router, prefix="/agent", tags=["agent"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(entities_router, prefix="/entities", tags=["entities"])
api_router.include_router(analyses_router, prefix="/analyses", tags=["analyses"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        dict: Health status information.
    """
    logger.info("health_check_called")
    return {"status": "healthy", "version": "1.0.0"}
