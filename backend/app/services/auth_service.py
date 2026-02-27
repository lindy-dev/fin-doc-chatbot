"""Authentication service utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User, UserRole

settings = get_settings()


def _encode_password(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password cannot be longer than 72 bytes for bcrypt")
    return password_bytes


def hash_password(password: str) -> str:
    """Hash a plaintext password."""

    password_bytes = _encode_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a hash."""

    password_bytes = _encode_password(password)
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


def _create_token(*, subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> tuple[str, int]:
    """Create an access token and return token + expiry seconds."""

    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    token = _create_token(subject=user_id, token_type="access", expires_delta=expires_delta)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(user_id: str) -> tuple[str, int]:
    """Create a refresh token and return token + expiry seconds."""

    expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    token = _create_token(subject=user_id, token_type="refresh", expires_delta=expires_delta)
    return token, int(expires_delta.total_seconds())


def decode_token(token: str) -> dict:
    """Decode a JWT token."""

    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""

    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by id."""

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def ensure_admin_seed(db: AsyncSession) -> Optional[User]:
    """Ensure an admin exists based on seed env vars."""

    if not (settings.admin_seed_email and settings.admin_seed_password and settings.admin_seed_name):
        return None

    existing = await get_user_by_email(db, settings.admin_seed_email)
    if existing:
        return existing

    admin = User(
        email=settings.admin_seed_email,
        name=settings.admin_seed_name,
        password_hash=hash_password(settings.admin_seed_password),
        role=UserRole.admin,
        is_approved=True,
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin
