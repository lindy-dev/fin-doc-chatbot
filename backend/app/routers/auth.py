"""Authentication and admin approval endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.user import User, UserRole
from app.schemas.auth import (
    ApproveUserRequest,
    LoginRequest,
    PendingUserResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_session: AsyncSession = Depends(get_db_session),
) -> User:
    """Get current user from access token."""

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await get_user_by_id(db_session, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return user


async def require_approved_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is approved."""

    if not current_user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not approved",
        )
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is admin."""

    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Register a new normal user (pending approval)."""

    existing = await get_user_by_email(db_session, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        role=UserRole.user,
        is_approved=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Login endpoint. Blocks unapproved users."""

    user = await get_user_by_email(db_session, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

    if not user.is_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not approved")

    access_token, access_expires = create_access_token(str(user.id))
    refresh_token, _ = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_expires,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get current user profile."""

    return UserResponse.model_validate(current_user)


@router.get("/admin/pending", response_model=List[PendingUserResponse])
async def list_pending_users(
    _: User = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[PendingUserResponse]:
    """List pending users."""

    result = await db_session.execute(
        select(User).where(User.is_approved.is_(False), User.role == UserRole.user)
    )
    users = result.scalars().all()
    return [PendingUserResponse.model_validate(user) for user in users]


@router.post("/admin/users/{user_id}/approval", response_model=UserResponse)
async def approve_user(
    user_id: str,
    payload: ApproveUserRequest,
    _: User = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """Approve or reject a user."""

    user = await get_user_by_id(db_session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot modify admin")

    user.is_approved = payload.is_approved
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db_session.commit()
    await db_session.refresh(user)
    return UserResponse.model_validate(user)
