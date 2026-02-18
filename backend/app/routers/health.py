"""Health check router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_redis
from app.database import get_db_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "financial-document-analyzer",
    }


@router.get("/db")
async def db_health_check(
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Database connectivity health check."""
    try:
        result = await db_session.execute(text("SELECT 1"))
        result.scalar_one()
        return {
            "status": "healthy",
            "service": "database",
            "connection": "active",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "service": "database",
                "error": str(e),
            },
        )


@router.get("/cache")
async def cache_health_check() -> dict:
    """Redis cache connectivity health check."""
    try:
        redis = await get_redis()
        await redis.ping()
        return {
            "status": "healthy",
            "service": "redis",
            "connection": "active",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "service": "redis",
                "error": str(e),
            },
        )


@router.get("/ready")
async def readiness_check(
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Readiness probe - checks all dependencies."""
    checks = {}
    all_healthy = True

    # Check database
    try:
        result = await db_session.execute(text("SELECT 1"))
        result.scalar_one()
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"
        all_healthy = False

    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"
        all_healthy = False

    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not ready",
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "checks": checks,
    }
