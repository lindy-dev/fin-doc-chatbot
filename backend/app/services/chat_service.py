"""Chat service for handling conversation logic."""

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import CacheService
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatMessageSchema, ConversationSchema


class ChatService:
    """Service for managing chat conversations."""

    def __init__(self, db_session: AsyncSession, cache: CacheService) -> None:
        self.db = db_session
        self.cache = cache

    async def get_or_create_conversation(
        self, session_id: str, title: Optional[str] = None
    ) -> Conversation:
        """Get existing conversation or create new one."""
        # Check cache first
        cached_id = await self.cache.get_conversation_id(session_id)
        if cached_id:
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == uuid.UUID(cached_id))
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation

        # Check database
        result = await self.db.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation:
            # Cache the ID
            await self.cache.set_conversation_id(session_id, str(conversation.id))
            return conversation

        # Create new conversation
        conversation = Conversation(
            session_id=session_id,
            title=title or "New Conversation",
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        # Cache the ID
        await self.cache.set_conversation_id(session_id, str(conversation.id))

        return conversation

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> Message:
        """Add a message to the conversation."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_=metadata or {},
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        # Invalidate message cache
        await self.cache.delete(f"chat:conversation:{conversation_id}:messages")

        return message

    async def get_conversation_history(
        self, conversation_id: uuid.UUID
    ) -> List[ChatMessageSchema]:
        """Get conversation history with caching."""
        # Check cache first
        cached = await self.cache.get_messages(str(conversation_id))
        if cached:
            return [ChatMessageSchema(**msg) for msg in cached]

        # Fetch from database
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()

        # Convert to schemas
        message_schemas = [
            ChatMessageSchema.model_validate(msg) for msg in messages
        ]

        # Cache the messages
        await self.cache.set_messages(
            str(conversation_id),
            [msg.model_dump() for msg in message_schemas],
        )

        return message_schemas

    async def get_conversation_by_session(
        self, session_id: str
    ) -> Optional[ConversationSchema]:
        """Get conversation by session ID."""
        result = await self.db.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        messages = await self.get_conversation_history(conversation.id)

        return ConversationSchema(
            id=conversation.id,
            session_id=conversation.session_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages,
        )

    async def delete_conversation(self, conversation_id: uuid.UUID) -> bool:
        """Delete a conversation and its messages."""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return False

        # Delete from database
        await self.db.delete(conversation)
        await self.db.commit()

        # Invalidate caches
        await self.cache.delete(f"chat:session:{conversation.session_id}:conversation")
        await self.cache.delete(f"chat:conversation:{conversation_id}:messages")

        return True
