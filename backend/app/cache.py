"""Redis cache client and utilities."""

import hashlib
import json
from typing import Any, Optional

import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

# Redis client instance
redis_client: Optional[redis.Redis] = None


async def init_redis() -> redis.Redis:
    """Initialize Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            str(settings.redis_url),
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def get_redis() -> redis.Redis:
    """Get or create Redis client."""
    return await init_redis()


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


class CacheService:
    """Service for caching data in Redis."""

    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache with optional TTL."""
        serialized = json.dumps(value, default=str)
        if ttl:
            await self.redis.setex(key, ttl, serialized)
        else:
            await self.redis.set(key, serialized)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self.redis.delete(key)

    async def get_conversation_id(self, session_id: str) -> Optional[str]:
        """Get conversation ID from session ID."""
        key = f"chat:session:{session_id}:conversation"
        return await self.get(key)

    async def set_conversation_id(
        self,
        session_id: str,
        conversation_id: str,
        ttl: int = 3600,
    ) -> None:
        """Cache conversation ID for session."""
        key = f"chat:session:{session_id}:conversation"
        await self.set(key, conversation_id, ttl)

    async def get_messages(self, conversation_id: str) -> Optional[list]:
        """Get cached messages for conversation."""
        key = f"chat:conversation:{conversation_id}:messages"
        return await self.get(key)

    async def set_messages(
        self,
        conversation_id: str,
        messages: list,
        ttl: int = 3600,
    ) -> None:
        """Cache messages for conversation."""
        key = f"chat:conversation:{conversation_id}:messages"
        await self.set(key, messages, ttl)

    def _generate_llm_cache_key(self, query: str, context: str = "") -> str:
        """Generate cache key for LLM response."""
        content = f"{query}:{context}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:32]
        return f"llm:cache:{hash_value}"

    async def get_llm_response(self, query: str, context: str = "") -> Optional[str]:
        """Get cached LLM response."""
        key = self._generate_llm_cache_key(query, context)
        return await self.get(key)

    async def set_llm_response(
        self,
        query: str,
        response: str,
        context: str = "",
        ttl: int = 86400,
    ) -> None:
        """Cache LLM response."""
        key = self._generate_llm_cache_key(query, context)
        await self.set(key, response, ttl)


async def get_cache_service() -> CacheService:
    """Get cache service instance."""
    redis = await get_redis()
    return CacheService(redis)
