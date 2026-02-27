"""Pydantic schemas for authentication and authorization."""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Register a new user."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response schema."""

    id: uuid.UUID
    email: EmailStr
    name: str
    role: Literal["admin", "user"]
    is_approved: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PendingUserResponse(BaseModel):
    """Pending user response."""

    id: uuid.UUID
    email: EmailStr
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApproveUserRequest(BaseModel):
    """Approve or reject a user."""

    is_approved: bool = True
    is_active: Optional[bool] = None
