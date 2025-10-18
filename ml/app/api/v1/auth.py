"""Session management endpoints for the API.

This module provides simplified endpoints for session management without authentication.
"""

import uuid
from typing import List

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from app.core.config import settings
from app.core.limiter import limiter
from app.core.logging import logger
from app.models.user import User
from app.schemas.auth import (
    SessionResponse,
    UserListResponse,
)
from app.services.database import DatabaseService
from app.utils.sanitization import (
    sanitize_string,
)

router = APIRouter()
db_service = DatabaseService()


@router.post("/session", response_model=SessionResponse)
async def create_session(user_id: int = 1, name: str = "New Session"):
    """Create a new chat session without authentication.

    Args:
        user_id: The user ID (default: 1)
        name: Optional session name (default: "New Session")

    Returns:
        SessionResponse: The session ID and name
    """
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Sanitize inputs
        sanitized_name = sanitize_string(name)

        # Check if user exists, create if not
        user = await db_service.get_user(user_id)
        if not user:
            # Auto-create user with unique username
            import time
            timestamp = int(time.time() * 1000)  # milliseconds
            username = f"user_{user_id}_{timestamp}"
            
            logger.info("auto_creating_user", requested_user_id=user_id, username=username)
            try:
                user = await db_service.create_user(
                    username=username,
                    password=User.hash_password(f"password_{user_id}")
                )
                logger.info("user_auto_created", actual_user_id=user.id, username=username)
                # Use the actual user ID from database
                user_id = user.id
            except Exception as e:
                logger.error("user_creation_failed", error=str(e), user_id=user_id)
                raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

        # Create session in database (use actual user_id)
        session = await db_service.create_session(session_id, user_id, sanitized_name)

        logger.info(
            "session_created",
            session_id=session_id,
            user_id=user_id,
            name=session.name,
        )

        return SessionResponse(session_id=session_id, name=session.name)
    except ValueError as ve:
        logger.error("session_creation_validation_failed", error=str(ve), user_id=user_id, exc_info=True)
        raise HTTPException(status_code=422, detail=str(ve))


@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(user_id: int = 1):
    """Get all session IDs for a user.

    Args:
        user_id: The user ID

    Returns:
        List[SessionResponse]: List of session IDs
    """
    try:
        sessions = await db_service.get_user_sessions(user_id)
        return [
            SessionResponse(
                session_id=sanitize_string(session.id),
                name=sanitize_string(session.name),
            )
            for session in sessions
        ]
    except ValueError as ve:
        logger.error("get_sessions_validation_failed", user_id=user_id, error=str(ve), exc_info=True)
        raise HTTPException(status_code=422, detail=str(ve))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session.

    Args:
        session_id: The ID of the session to delete

    Returns:
        dict: Success message
    """
    try:
        # Sanitize inputs
        sanitized_session_id = sanitize_string(session_id)

        # Delete the session
        await db_service.delete_session(sanitized_session_id)

        logger.info("session_deleted", session_id=session_id)
        return {"message": "Session deleted successfully"}
    except ValueError as ve:
        logger.error("session_deletion_validation_failed", error=str(ve), session_id=session_id, exc_info=True)
        raise HTTPException(status_code=422, detail=str(ve))


@router.get("/users", response_model=UserListResponse)
async def get_all_users():
    """Get all users in the system.
    
    Returns:
        UserListResponse: List of all users with total count
    """
    try:
        users = await db_service.get_all_users()
        
        from app.schemas.auth import UserInfo
        user_infos = [UserInfo.model_validate(user) for user in users]
        
        return UserListResponse(users=user_infos, total=len(user_infos))
    except Exception as e:
        logger.error("get_users_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
