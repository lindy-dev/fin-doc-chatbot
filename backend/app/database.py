"""Database connection and session management."""

import logging
import socket
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import get_settings
from app.models.base import Base

logger = logging.getLogger(__name__)
settings = get_settings()

# Log database URL for debugging (mask password)
db_url = str(settings.database_url)
logger.info(f"[DIAGNOSTIC] Database URL: {db_url}")
try:
    parsed_url = make_url(db_url)
    logger.info(
        "[DIAGNOSTIC] Parsed DB URL - driver=%s, user=%s, host=%s, port=%s, db=%s",
        parsed_url.drivername,
        parsed_url.username,
        parsed_url.host,
        parsed_url.port,
        parsed_url.database,
    )
    if parsed_url.host and parsed_url.port:
        try:
            addr_info = socket.getaddrinfo(
                parsed_url.host,
                parsed_url.port,
                type=socket.SOCK_STREAM,
            )
            logger.info(
                "[DIAGNOSTIC] Host resolution for %s:%s -> %s",
                parsed_url.host,
                parsed_url.port,
                [(ai[0], ai[4]) for ai in addr_info],
            )
        except Exception as e:
            logger.error(
                "[DIAGNOSTIC] Host resolution failed for %s:%s: %s",
                parsed_url.host,
                parsed_url.port,
                e,
            )
except Exception as e:
    logger.error(f"[DIAGNOSTIC] Failed to parse DB URL: {type(e).__name__}: {e}")
logger.info(f"[DIAGNOSTIC] App environment: {settings.app_env}")
logger.info(f"[DIAGNOSTIC] Debug mode: {settings.debug}")

# Create async engine
# For local development, disable SSL to prevent handshake failures with PostgreSQL
# that doesn't have SSL certificates configured.
# asyncpg defaults to attempting SSL, which causes "unexpected connection_lost()" errors.
connect_args = {"ssl": False} if settings.is_development else {}
logger.info(f"[DIAGNOSTIC] Using connect_args: {connect_args}")

engine = create_async_engine(
    str(settings.database_url),
    echo=settings.debug,
    future=True,
    connect_args=connect_args,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    logger.info("[DIAGNOSTIC] init_db() called - attempting to connect to database...")
    try:
        async with engine.begin() as conn:
            logger.info("[DIAGNOSTIC] Database connection established successfully")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("[DIAGNOSTIC] Database tables created/verified")
    except Exception as e:
        logger.error(f"[DIAGNOSTIC] init_db() failed: {type(e).__name__}: {e}")
        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
