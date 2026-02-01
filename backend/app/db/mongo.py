from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import FastAPI

from app.core.config import get_settings


class MongoClientManager:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncIOMotorClient(settings.mongodb_url)
        self._db = self._client[settings.mongodb_db]

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db

    async def close(self) -> None:
        self._client.close()


def setup_mongo(app: FastAPI) -> AsyncIOMotorDatabase:
    manager = MongoClientManager()
    app.state.mongo = manager

    @app.on_event("shutdown")
    async def shutdown_event() -> None:  # pragma: no cover - lifecycle hook
        await manager.close()

    return manager.db

