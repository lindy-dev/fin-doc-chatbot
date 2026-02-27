"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache import close_redis, init_redis
from app.config import get_settings
from app.database import close_db, get_db_context, init_db
from app.routers import auth, chat, health
from app.services.auth_service import ensure_admin_seed

settings = get_settings()


def setup_logging() -> None:
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
            if not settings.is_development
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set logging level
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level.upper()),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger = structlog.get_logger()
    logger.info("Starting up Financial Document Analyzer API")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Seed admin user if configured
    async with get_db_context() as db_session:
        admin = await ensure_admin_seed(db_session)
        if admin:
            logger.info("Admin seed ensured", email=admin.email)

    # Initialize Redis
    await init_redis()
    logger.info("Redis cache initialized")

    yield

    # Shutdown
    logger.info("Shutting down Financial Document Analyzer API")

    # Close database connections
    await close_db()
    logger.info("Database connections closed")

    # Close Redis connection
    await close_redis()
    logger.info("Redis connection closed")


# Create FastAPI application
app = FastAPI(
    title="Financial Document Analyzer API",
    description="AI-powered financial document analysis with multi-agent CrewAI system",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Financial Document Analyzer API",
        "version": "0.1.0",
        "docs": "/docs" if settings.is_development else None,
    }
