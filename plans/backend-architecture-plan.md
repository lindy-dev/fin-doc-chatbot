# Financial Document Analyzer - Backend Architecture Plan

## Overview
MVP Backend with FastAPI, Postgres, Redis, CrewAI multi-agent system, and SSE chat streaming.

## System Architecture

```mermaid
flowchart TB
    Client[Client/Browser] -->|SSE /chat/stream| FastAPI[FastAPI Application]
    FastAPI -->|Cache Read/Write| Redis[(Redis Cache)]
    FastAPI -->|CRUD Operations| Postgres[(PostgreSQL)]
    FastAPI -->|Delegate Analysis| CrewAI[CrewAI Multi-Agent Crew]
    CrewAI -->|LLM Calls| OpenAI[OpenAI API]

    subgraph "CrewAI Financial Analysis Crew"
        Agent1[Data Analyst Agent]
        Agent2[Financial Advisor Agent]
        Agent3[Risk Assessor Agent]
    end

    subgraph "Data Layer"
        Conversations[Conversations Table]
        Messages[Messages Table]
        CacheData[Cached Responses]
    end

    CrewAI --> Agent1
    CrewAI --> Agent2
    CrewAI --> Agent3
    Postgres --> Conversations
    Postgres --> Messages
    Redis --> CacheData
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | Async API with auto-generated docs |
| Database | PostgreSQL + SQLAlchemy | Persistent storage |
| Cache | Redis | Conversation & LLM response caching |
| AI Framework | CrewAI 0.130.0 | Multi-agent orchestration |
| LLM Provider | OpenAI (GPT-4/GPT-3.5) | Language model |
| Streaming | Server-Sent Events | Real-time chat streaming |
| Containerization | Docker + Docker Compose | Local development |

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings & environment variables
│   ├── database.py             # DB connection & session management
│   ├── cache.py                # Redis cache client
│   ├── models/
│   │   ├── __init__.py
│   │   ├── conversation.py     # Conversation & Message models
│   │   └── base.py             # SQLAlchemy base
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py             # Pydantic schemas for chat
│   │   └── common.py           # Shared schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py             # Chat streaming endpoints
│   │   └── health.py           # Health check endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py     # Chat business logic
│   │   ├── cache_service.py    # Caching utilities
│   │   └── crew_service.py     # CrewAI orchestration
│   └── crew/
│       ├── __init__.py
│       ├── agents.py           # Agent definitions
│       ├── tasks.py            # Task definitions
│       └── crew.py             # Crew assembly
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml              # Dependencies
└── .env.example                # Environment template
```

## Database Schema

### Conversations Table
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversations_session_id ON conversations(session_id);
```

### Messages Table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

## CrewAI Multi-Agent Design

### Agents

1. **Data Analyst Agent**
   - Role: Financial data interpreter
   - Goal: Extract and analyze numerical data from queries
   - Tools: Calculation, trend analysis

2. **Financial Advisor Agent**
   - Role: Investment strategist
   - Goal: Provide actionable financial recommendations
   - Tools: Market research, portfolio analysis

3. **Risk Assessor Agent**
   - Role: Risk evaluator
   - Goal: Identify and quantify financial risks
   - Tools: Risk metrics, scenario analysis

### Task Flow
```mermaid
flowchart LR
    Query[User Query] --> Analyst[Data Analyst]
    Analyst --> Advisor[Financial Advisor]
    Advisor --> Risk[Risk Assessor]
    Risk --> Response[Final Response]
```

## API Endpoints

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/stream` | SSE streaming chat endpoint |
| GET | `/chat/history/{session_id}` | Get conversation history |
| DELETE | `/chat/{conversation_id}` | Delete conversation |

### Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Application health check |
| GET | `/health/db` | Database connectivity check |
| GET | `/health/cache` | Redis connectivity check |

## Caching Strategy

### Redis Key Patterns

```
# Conversation cache
chat:session:{session_id}:conversation -> conversation_id

# Message history cache (TTL: 1 hour)
chat:conversation:{conversation_id}:messages -> List[Message]

# LLM response cache (TTL: 24 hours)
llm:cache:{hash(query+context)} -> response
```

### Cache Invalidation
- Messages: Updated on new message, 1 hour TTL
- LLM responses: 24 hour TTL for similar queries

## SSE Streaming Protocol

### Request
```http
POST /chat/stream
Content-Type: application/json

{
  "session_id": "uuid-string",
  "message": "Analyze Tesla's Q2 revenue trends"
}
```

### Response Stream
```
data: {"type": "status", "content": "analyzing"}

data: {"type": "chunk", "content": "Based on the data..."}

data: {"type": "chunk", "content": " revenue shows..."}

data: {"type": "complete", "content": "Full response", "metadata": {...}}
```

## Environment Variables

```env
# App
APP_ENV=development
DEBUG=true
LOG_LEVEL=info

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/financial_analyzer

# Redis
REDIS_URL=redis://redis:6379/0

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# CrewAI
CREWAI_VERBOSE=true
```

## Implementation Checklist

- [ ] Update pyproject.toml with all dependencies
- [ ] Create Dockerfile for FastAPI
- [ ] Create docker-compose.yml with Postgres + Redis
- [ ] Set up SQLAlchemy models with async support
- [ ] Configure Redis client with async redis-py
- [ ] Define CrewAI agents and tasks
- [ ] Implement SSE streaming endpoint
- [ ] Add caching middleware for conversations
- [ ] Add caching for LLM responses
- [ ] Create health check endpoints
- [ ] Add structured logging
- [ ] Create .env.example template
