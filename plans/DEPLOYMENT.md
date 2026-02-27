# Deployment Guide - FinDocAnalyzer

## Overview

Deploy FinDocAnalyzer using:
- **Railway** for backend (FastAPI + PostgreSQL + Redis)
- **Netlify** for frontend (React + Vite)

---

## Railway Backend Deployment

### 1. Initial Setup

#### Create Railway Account
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login
```

#### Initialize Project
```bash
cd backend
railway init
# Select "Create new project" → name: "findoc-analyzer"
```

### 2. Provision Services

Add PostgreSQL:
```bash
railway add --database postgresql
# Note the connection string: ${{Postgres.DATABASE_URL}}
```

Add Redis:
```bash
railway add --database redis
# Note the connection string: ${{Redis.REDIS_URL}}
```

### 3. Environment Variables

Set in Railway Dashboard or CLI:

```bash
# Database
railway variables set DATABASE_URL="${{Postgres.DATABASE_URL}}"
railway variables set REDIS_URL="${{Redis.REDIS_URL}}"

# Security
railway variables set SECRET_KEY="$(openssl rand -hex 32)"
railway variables set ALGORITHM="HS256"
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="30"

# OpenAI (for CrewAI)
railway variables set OPENAI_API_KEY="sk-..."

# External APIs
railway variables set ALPHA_VANTAGE_API_KEY="..."

# App Settings
railway variables set UPLOAD_DIR="/app/uploads"
railway variables set MAX_FILE_SIZE="10485760"
railway variables set DOCUMENT_RETENTION_DAYS="30"
railway variables set CACHE_TTL_SECONDS="3600"

# CORS (Netlify URL)
railway variables set CORS_ORIGINS="https://findoc-analyzer.netlify.app"
```

### 4. Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads

# Run migrations and start
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 5. railway.toml

Create `backend/railway.toml`:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### 6. Deploy

```bash
cd backend
railway up

# View logs
railway logs

# Open in browser
railway open
```

### 7. Custom Domain (Optional)

```bash
railway domain
# Add custom domain in Railway dashboard
# Update DNS with provided records
```

---

## Netlify Frontend Deployment

### 1. Build Settings

Create `frontend/netlify.toml`:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/api/*"
  to = "https://api.findoc-analyzer.railway.app/api/:splat"
  status = 200

[[redirects]]
  from = "/ws/*"
  to = "wss://api.findoc-analyzer.railway.app/ws/:splat"
  status = 200

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### 2. Environment Variables

Set in Netlify Dashboard → Site Settings → Environment Variables:

```
VITE_API_URL=https://api.findoc-analyzer.railway.app
VITE_WS_URL=wss://api.findoc-analyzer.railway.app
```

### 3. Deploy via Git

Push to GitHub, then:

1. Connect Netlify to GitHub repo
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Deploy!

### 4. Deploy via CLI

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Initialize
cd frontend
netlify init
# Select "Create & configure a new site"

# Deploy
netlify deploy --prod
```

---

## Docker Compose (Local Development)

Create root `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: findoc-postgres
    environment:
      POSTGRES_USER: findoc
      POSTGRES_PASSWORD: findoc_pass
      POSTGRES_DB: findoc
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U findoc"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: findoc-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: findoc-backend
    environment:
      DATABASE_URL: postgresql://findoc:findoc_pass@postgres:5432/findoc
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: dev-secret-key-change-in-production
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ALPHA_VANTAGE_API_KEY: ${ALPHA_VANTAGE_API_KEY}
      UPLOAD_DIR: /app/uploads
      MAX_FILE_SIZE: 10485760
      DOCUMENT_RETENTION_DAYS: 30
      CACHE_TTL_SECONDS: 3600
      CORS_ORIGINS: "http://localhost:5173,http://localhost:3000"
    volumes:
      - ./backend:/app
      - uploads_data:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    command: |
      sh -c "alembic upgrade head && 
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  # Frontend (Vite Dev Server)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: findoc-frontend
    environment:
      VITE_API_URL: http://localhost:8000
      VITE_WS_URL: ws://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    command: npm run dev -- --host

  # Optional: pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: findoc-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@findoc.local
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

  # Optional: Redis Commander for cache management
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: findoc-redis-commander
    environment:
      REDIS_HOSTS: local:redis:6379
    ports:
      - "8081:8081"
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
  uploads_data:
```

### Development Dockerfile

Create `backend/Dockerfile.dev`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

Create `frontend/Dockerfile.dev`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

### Makefile Commands

Create root `Makefile`:

```makefile
.PHONY: dev build up down logs migrate test clean

# Development
dev:
	docker-compose up -d

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

# Database
migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Migration message: " message; \
	docker-compose exec backend alembic revision --autogenerate -m "$$message"

# Testing
test-backend:
	docker-compose exec backend pytest

test-frontend:
	docker-compose exec frontend npm test

# Utilities
shell-backend:
	docker-compose exec backend bash

shell-frontend:
	docker-compose exec frontend sh

clean:
	docker-compose down -v
	docker system prune -f

# Production build
build:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# One-time setup
setup: dev
	@echo "Waiting for database..."
	@sleep 5
	make migrate
	@echo "Setup complete!"
```

---

## Environment Configuration

### Development (.env.development)

```env
# Backend
DATABASE_URL=postgresql://findoc:findoc_pass@localhost:5432/findoc
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-not-for-production
OPENAI_API_KEY=sk-...
ALPHA_VANTAGE_API_KEY=...

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Production (.env.production)

```env
# Set these in Railway/Netlify dashboard, not in files!
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      
      - name: Run tests
        run: |
          cd frontend
          npm test
      
      - name: Build
        run: |
          cd frontend
          npm run build

  deploy-backend:
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        uses: railway/cli-deploy@v1
        with:
          project: findoc-analyzer
          service: backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  deploy-frontend:
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Netlify
        uses: netlify/actions/cli@master
        with:
          args: deploy --prod
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

---

## Monitoring & Logging

### Railway Monitoring

Built-in metrics available at:
- CPU/Memory usage
- Request logs
- Error tracking
- Database metrics

Add health check endpoint in FastAPI:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_db_connection(),
        "redis": check_redis_connection(),
        "timestamp": datetime.utcnow()
    }
```

### Netlify Analytics

Enable in Site Settings → Analytics:
- Page views
- Unique visitors
- Top pages
- Performance metrics

---

## Scaling Considerations

### Railway (Backend)

**Current (< 100 users):**
- 1 CPU, 512MB RAM sufficient
- Free tier PostgreSQL (500 hours/month)
- Free tier Redis (500 hours/month)

**Future scaling:**
- Upgrade to Pro plan
- Add background worker service for analysis jobs
- Use Redis for distributed task queue
- Scale PostgreSQL with read replicas

### Netlify (Frontend)

**Current:**
- Free tier sufficient for < 100 users
- 100GB bandwidth/month
- 300 build minutes/month

**Future:**
- Upgrade to Pro for team features
- Add edge functions for API proxying

---

## Security Checklist

- ✅ JWT tokens with expiration
- ✅ CORS configured for specific origins
- ✅ Rate limiting on API endpoints
- ✅ File size limits (10MB)
- ✅ File type validation
- ✅ Database connection pooling
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS protection (React escapes by default)
- ✅ HTTPS enforced in production
- ✅ Secrets in environment variables (never in code)

---

## Troubleshooting

### Railway Deployment Issues

```bash
# View detailed logs
railway logs -f

# SSH into container for debugging
railway connect

# Restart service
railway up --detach
```

### Database Connection Issues

```bash
# Test connection from local
psql ${{Postgres.DATABASE_URL}}

# Check migrations
railway run alembic current
railway run alembic history
```

### CORS Errors

Verify `CORS_ORIGINS` includes your Netlify URL exactly (including https://)

### File Upload Issues

Check upload directory exists and has correct permissions:
```bash
railway run ls -la /app/uploads
```

---

## Cost Estimation

### Railway (Backend)

| Component | Plan | Monthly Cost |
|-----------|------|--------------|
| API Server | Starter (1 CPU, 512MB) | ~$5 |
| PostgreSQL | Starter | ~$5 |
| Redis | Starter | ~$0 (included) |
| **Total** | | **~$10/month** |

### Netlify (Frontend)

| Tier | Cost |
|------|------|
| Free | $0 |
| Pro (if needed) | $19/month |

### External APIs

| Service | Estimated Monthly Cost |
|---------|----------------------|
| OpenAI (CrewAI) | ~$20-50 (depends on usage) |
| Alpha Vantage | $0 (free tier) |

**Total Estimated: $30-80/month**

---

## Next Steps

1. **Set up Railway account** and create project
2. **Add PostgreSQL and Redis** services
3. **Configure environment variables**
4. **Deploy backend** with `railway up`
5. **Set up Netlify** and deploy frontend
6. **Configure custom domain** (optional)
7. **Set up GitHub Actions** for CI/CD
8. **Monitor and optimize**

**Ready to go live!** 🚀
