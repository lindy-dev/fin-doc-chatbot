# Financial Document Analyzer - Backend

FastAPI backend with CrewAI multi-agent financial analysis, PostgreSQL persistence, and Redis caching.

## Features

- **SSE Chat Streaming**: Real-time chat responses using Server-Sent Events
- **Multi-Agent CrewAI**: 3 specialized agents (Data Analyst, Financial Advisor, Risk Assessor)
- **PostgreSQL**: Async SQLAlchemy with conversation and message storage
- **Redis Caching**: Caches conversations (1hr TTL) and LLM responses (24hr TTL)
- **Docker Compose**: Complete stack with Postgres + Redis + FastAPI

## Quick Start

### Using Docker Compose (Recommended)

1. Copy environment file:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

2. Start the stack:
```bash
docker-compose up -d
```

3. Access the API:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Local Development

1. Install dependencies:
```bash
pip install uv
uv pip install -e ".[dev]"
```

2. Start Postgres and Redis:
```bash
docker-compose up -d postgres redis
```

3. Run the app:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Chat
- `POST /chat/stream` - SSE streaming chat (send JSON: `{session_id, message, context}`)
- `GET /chat/history/{session_id}` - Get conversation history
- `DELETE /chat/{conversation_id}` - Delete conversation

### Health
- `GET /health` - Basic health check
- `GET /health/db` - Database health
- `GET /health/cache` - Redis health
- `GET /health/ready` - Readiness probe

## Example Usage

### Stream Chat Request
```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user-123",
    "message": "Analyze Tesla Q2 2025 revenue trends",
    "context": "Focus on EV market growth"
  }'
```

### SSE Response Format
```
data: {"type": "status", "content": "Analyzing your query..."}
data: {"type": "chunk", "content": "Based on the analysis..."}
data: {"type": "complete", "content": "Full response...", "metadata": {...}}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/production) | development |
| `DATABASE_URL` | PostgreSQL connection string | postgresql+asyncpg://... |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `OPENAI_API_KEY` | OpenAI API key | required |
| `OPENAI_MODEL` | LLM model | gpt-4 |
| `CACHE_TTL_CONVERSATION` | Conversation cache TTL (seconds) | 3600 |
| `CACHE_TTL_LLM` | LLM response cache TTL (seconds) | 86400 |

## Architecture

```
Client → FastAPI → CrewAI Crew → OpenAI
           ↓           ↓
        Postgres    Redis Cache
```

### CrewAI Agents
1. **Data Analyst**: Extracts and analyzes financial metrics
2. **Financial Advisor**: Provides investment recommendations
3. **Risk Assessor**: Identifies and quantifies risks

## Project Structure

```
app/
├── main.py           # FastAPI entry point
├── config.py         # Settings
├── database.py       # Postgres connection
├── cache.py          # Redis client
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── routers/          # API endpoints
├── services/         # Business logic
└── crew/             # CrewAI agents & tasks
```
