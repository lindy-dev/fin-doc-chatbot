"""Pydantic schemas for chat endpoints."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat messages."""

    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    context: Optional[str] = Field(None, description="Additional context for the query")


class ChatStreamEvent(BaseModel):
    """Base schema for SSE stream events."""

    type: Literal["status", "chunk", "complete", "error"] = Field(
        ..., description="Event type"
    )
    content: str = Field(..., description="Event content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatMessageSchema(BaseModel):
    """Schema for chat messages."""

    id: uuid.UUID
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata_")

    class Config:
        from_attributes = True
        populate_by_name = True


class ConversationSchema(BaseModel):
    """Schema for conversations."""

    id: uuid.UUID
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageSchema] = []

    class Config:
        from_attributes = True


class ConversationListSchema(BaseModel):
    """Schema for conversation list response."""

    conversations: List[ConversationSchema]
    total: int


class ChatHistoryResponse(BaseModel):
    """Response schema for chat history."""

    session_id: str
    conversation_id: uuid.UUID
    messages: List[ChatMessageSchema]
