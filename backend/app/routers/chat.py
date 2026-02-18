"""Chat router with SSE streaming endpoint."""

import asyncio
import json
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import CacheService, get_cache_service
from app.config import get_settings
from app.crew.crew import get_financial_crew
from app.database import get_db_session
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatStreamEvent,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

ROUTER_SYSTEM_PROMPT = """You are a router that decides whether a query requires complex, multi-agent financial analysis.
Return JSON only with a single key 'route' set to 'crewai' for complex analysis or 'chat' for simple Q&A.
Choose 'crewai' when the query asks for multi-step analysis, comparisons, risk assessment, portfolio strategy, or synthesis.
Choose 'chat' for simple factual or conversational responses."""


def _send_event(event_type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    event = ChatStreamEvent(type=event_type, content=content, metadata=metadata)
    return f"data: {json.dumps(event.model_dump())}\n\n"


def _stringify_attr(value: object | None) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if hasattr(value, "role"):
        return str(getattr(value, "role"))
    if hasattr(value, "description"):
        return str(getattr(value, "description"))
    return str(value)


def _chunk_text(text: str, chunk_size: int = 50) -> list[str]:
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


async def _route_request(message: str, context: str) -> str:
    classification = await openai_client.chat.completions.create(
        model=settings.openai_classifier_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Message: {message}\nContext: {context or 'None'}",
            },
        ],
    )
    content = classification.choices[0].message.content or "{}"
    parsed = json.loads(content)
    route = parsed.get("route", "chat")
    return "crewai" if route == "crewai" else "chat"


async def _stream_openai_chat(
    request: ChatRequest,
    cached_response: Optional[str],
    response_parts: list[str],
) -> AsyncGenerator[str, None]:
    if cached_response:
        response_parts.append(cached_response)
        yield _send_event(
            "status",
            "Retrieving cached response...",
            {"route": "chat"},
        )
        for chunk in _chunk_text(cached_response):
            yield _send_event("chunk", chunk)
        return

    yield _send_event("status", "Generating response...", {"route": "chat"})

    messages = [
        {"role": "system", "content": "You are a helpful financial assistant."},
    ]
    if request.context:
        messages.append({"role": "system", "content": f"Context: {request.context}"})
    messages.append({"role": "user", "content": request.message})

    stream = await openai_client.chat.completions.create(
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        stream=True,
        messages=messages,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if not delta or not delta.content:
            continue
        response_parts.append(delta.content)
        yield _send_event("chunk", delta.content)


async def _stream_crewai_analysis(
    request: ChatRequest,
    cached_response: Optional[str],
    response_parts: list[str],
) -> AsyncGenerator[str, None]:
    crew = get_financial_crew()

    if cached_response:
        response_parts.append(cached_response)
        yield _send_event(
            "status",
            "Retrieving cached analysis...",
            {"route": "crewai"},
        )
        for chunk in _chunk_text(cached_response):
            yield _send_event("chunk", chunk)
        return

    yield _send_event(
        "status",
        "Running multi-agent analysis...",
        {"route": "crewai"},
    )

    queue: asyncio.Queue[str] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def progress_callback(status: str) -> None:
        event = _send_event("progress", status, {"route": "crewai"})
        loop.call_soon_threadsafe(queue.put_nowait, event)

    def step_callback(step: object) -> None:
        metadata = {
            "route": "crewai",
            "agent": _stringify_attr(getattr(step, "agent", None)),
            "task": _stringify_attr(getattr(step, "task", None)),
            "step": _stringify_attr(getattr(step, "name", None))
            or _stringify_attr(getattr(step, "description", None)),
        }
        content = _stringify_attr(getattr(step, "description", None)) or str(step)
        event = _send_event("progress", content, metadata)
        loop.call_soon_threadsafe(queue.put_nowait, event)

    analysis_task = asyncio.create_task(
        crew.analyze(
            request.message,
            request.context or "",
            progress_callback,
            step_callback=step_callback,
        )
    )

    while not analysis_task.done() or not queue.empty():
        try:
            event = await asyncio.wait_for(queue.get(), timeout=0.1)
            yield event
        except asyncio.TimeoutError:
            continue

    result = await analysis_task
    response_parts.append(result)
    for chunk in _chunk_text(result):
        yield _send_event("chunk", chunk)




async def generate_chat_stream(
    request: ChatRequest,
    db_session: AsyncSession,
    cache: CacheService,
) -> AsyncGenerator[str, None]:
    """Generate SSE stream for chat response."""
    chat_service = ChatService(db_session, cache)

    try:
        # Get or create conversation
        conversation = await chat_service.get_or_create_conversation(
            request.session_id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
        )

        # Save user message
        await chat_service.add_message(
            conversation.id,
            "user",
            request.message,
        )

        # Send status update
        yield _send_event("status", "Analyzing your query...")

        cached_response = await cache.get_llm_response(
            request.message, request.context or ""
        )

        route = await _route_request(request.message, request.context or "")
        response_parts: list[str] = []

        if route == "crewai":
            stream = _stream_crewai_analysis(
                request,
                cached_response,
                response_parts,
            )
        else:
            stream = _stream_openai_chat(
                request,
                cached_response,
                response_parts,
            )

        async for event in stream:
            yield event

        response_content = "".join(response_parts)

        if not cached_response:
            await cache.set_llm_response(
                request.message,
                response_content,
                request.context or "",
            )

        yield _send_event(
            "complete",
            response_content,
            {"conversation_id": str(conversation.id), "cached": cached_response is not None},
        )

        await chat_service.add_message(
            conversation.id,
            "assistant",
            response_content,
            metadata={"cached": cached_response is not None, "route": route},
        )

    except Exception as e:
        # Send error event
        error_event = ChatStreamEvent(
            type="error",
            content=str(e),
            metadata={"error_type": type(e).__name__},
        )
        yield f"data: {json.dumps(error_event.model_dump())}\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db_session: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service),
) -> StreamingResponse:
    """Stream chat response using Server-Sent Events.

    This endpoint accepts a chat message and streams the AI response
    using Server-Sent Events (SSE). The response is generated by a
    multi-agent CrewAI system specialized in financial analysis.
    """
    return StreamingResponse(
        generate_chat_stream(request, db_session, cache),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service),
) -> ChatHistoryResponse:
    """Get chat history for a session."""
    chat_service = ChatService(db_session, cache)
    conversation = await chat_service.get_conversation_by_session(session_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ChatHistoryResponse(
        session_id=session_id,
        conversation_id=conversation.id,
        messages=conversation.messages,
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    db_session: AsyncSession = Depends(get_db_session),
    cache: CacheService = Depends(get_cache_service),
) -> dict:
    """Delete a conversation and its messages."""
    chat_service = ChatService(db_session, cache)
    deleted = await chat_service.delete_conversation(conversation_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted successfully"}
