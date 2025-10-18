"""This file contains the authentication schema for the application."""

import re
from datetime import datetime
from typing import List

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class Token(BaseModel):
    """Token model for authentication.

    Attributes:
        access_token: The JWT access token.
        token_type: The type of token (always "bearer").
        expires_at: The token expiration timestamp.
    """

    access_token: str = Field(..., description="The JWT access token")
    token_type: str = Field(default="bearer", description="The type of token")
    expires_at: datetime = Field(..., description="The token expiration timestamp")


class TokenResponse(BaseModel):
    """Response model for login endpoint.

    Attributes:
        access_token: The JWT access token
        token_type: The type of token (always "bearer")
        expires_at: When the token expires
    """

    access_token: str = Field(..., description="The JWT access token")
    token_type: str = Field(default="bearer", description="The type of token")
    expires_at: datetime = Field(..., description="When the token expires")


class UserCreate(BaseModel):
    """Request model for user registration.

    Attributes:
        username: User's username
        password: User's password (any text)
    """

    username: str = Field(..., description="User's username", min_length=1, max_length=64)
    password: str = Field(..., description="User's password", min_length=1)


class UserResponse(BaseModel):
    """Response model for user operations.

    Attributes:
        id: User's ID
        username: User's username
        token: Authentication token
    """

    id: int = Field(..., description="User's ID")
    username: str = Field(..., description="User's username")
    token: Token = Field(..., description="Authentication token")


class SessionResponse(BaseModel):
    """Response model for session creation.

    Attributes:
        session_id: The unique identifier for the chat session
        name: Name of the session (defaults to empty string)
    """

    session_id: str = Field(..., description="The unique identifier for the chat session")
    name: str = Field(default="", description="Name of the session", max_length=100)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Sanitize the session name.

        Args:
            v: The name to sanitize

        Returns:
            str: The sanitized name
        """
        # Remove any potentially harmful characters
        sanitized = re.sub(r'[<>{}[\]()\'"`]', "", v)
        return sanitized


class UserInfo(BaseModel):
    """User information model.
    
    Attributes:
        id: User's ID
        username: User's username
        created_at: When the user was created
    """
    
    id: int = Field(..., description="User's ID")
    username: str = Field(..., description="User's username")
    created_at: datetime = Field(..., description="When the user was created")
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response model for listing users.
    
    Attributes:
        users: List of users
        total: Total number of users
    """
    
    users: List[UserInfo] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
