# Unified Docker Compose Plan with Nginx Reverse Proxy

## Goal

Create a single Docker Compose configuration that launches both the frontend React app and the backend FastAPI app together with all required dependencies (PostgreSQL, Redis), fronted by an Nginx reverse proxy for a production-like setup.

## Architecture Overview

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        NG[nginx<br/>Reverse Proxy<br/>Port: 80]
        FE[frontend<br/>React + Vite<br/>Port: 5174]
        BE[backend<br/>FastAPI + Uvicorn<br/>Port: 8000]
        PG[postgres<br/>PostgreSQL 16<br/>Port: 5431]
        RD[redis<br/>Redis 7<br/>Port: 6379]
    end

    User -->|http://localhost| NG
    NG -->|/api/*| BE
    NG -->|/*| FE
    BE -->|Database| PG
    BE -->|Cache| RD
```

## Service Details

### 1. Nginx Service (NEW)

- **Image**: `nginx:alpine`
- **Port**: 80 (mapped to host)
- **Purpose**: Reverse proxy routing `/api/*` to backend and all other traffic to frontend
- **Config**: Custom `nginx.conf` with proxy rules

### 2. Frontend Service

- **Base Image**: `node:20-alpine`
- **Port**: 5174 (internal only, accessed via nginx)
- **Working Directory**: `/app`
- **Commands**: `npm install` → `npm run dev`
- **Environment**: `VITE_API_BASE_URL=/api` (relative path through nginx)
- **Volumes**: `./frontend:/app` (for hot-reload)

### 3. Backend Service

- **Base Image**: `python:3.11-slim`
- **Port**: 8000 (internal only, accessed via nginx)
- **Working Directory**: `/app`
- **Dependencies**: PostgreSQL, Redis
- **Environment**: All existing env vars from `.env`
- **Volumes**: `./backend/app:/app/app` (for hot-reload)

### 4. PostgreSQL Service

- **Image**: `postgres:16-alpine`
- **Port**: 5431 (mapped to host)
- **Database**: `financial_analyzer`
- **User**: `finuser`
- **Password**: `finpass`

### 5. Redis Service

- **Image**: `redis:7-alpine`
- **Port**: 6379 (mapped to host)

## File Structure

```
fin-doc-chatbot/
├── docker-compose.yml          # NEW: Root-level unified compose
├── nginx/
│   ├── Dockerfile              # NEW: Nginx container config
│   └── nginx.conf              # NEW: Nginx reverse proxy config
├── frontend/
│   ├── Dockerfile              # NEW: Frontend container config
│   ├── .dockerignore           # NEW: Optimize build context
│   └── vite.config.ts          # MODIFIED: Allow external connections
└── backend/
    ├── Dockerfile              # EXISTING: (minor tweaks needed)
    └── docker-compose.yml      # EXISTING: (can be deprecated)
```

## Implementation Steps

### Step 1: Create Nginx Directory and Config

**Path**: `nginx/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;

    # Frontend - all traffic except /api
    location / {
        proxy_pass http://frontend:5174;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # WebSocket support for Vite HMR
        proxy_read_timeout 86400;
    }

    # Backend API - all /api/* requests
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Path**: `nginx/Dockerfile`

```dockerfile
FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Step 2: Create Frontend Dockerfile

**Path**: `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose Vite dev server port
EXPOSE 5174

# Run dev server with host binding for container access
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### Step 3: Create Frontend .dockerignore

**Path**: `frontend/.dockerignore`

```
node_modules
npm-debug.log
dist
.git
.env
*.md
```

### Step 4: Update Vite Config

**Path**: `frontend/vite.config.ts`

```typescript
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    host: "0.0.0.0", // ADD: Allow external connections
    strictPort: true, // ADD: Fail if port is taken
    watch: {
      usePolling: true, // ADD: Required for Docker volume mounts
    },
    hmr: {
      clientPort: 80, // ADD: Tell client to connect through nginx port
    },
  },
});
```

### Step 5: Create Root docker-compose.yml

**Path**: `docker-compose.yml`

```yaml
version: "3.8"

services:
  # Nginx Reverse Proxy
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: fin-doc-nginx
    ports:
      - "80:80"
    depends_on:
      - frontend
      - backend
    networks:
      - fin-doc-network

  # Frontend React App
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: fin-doc-frontend
    environment:
      - VITE_API_BASE_URL=/api # Relative path through nginx
    expose:
      - "5174" # Only exposed to nginx, not host
    volumes:
      - ./frontend:/app
      - /app/node_modules # Anonymous volume to preserve node_modules
    depends_on:
      - backend
    networks:
      - fin-doc-network

  # Backend FastAPI App
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: fin-doc-backend
    environment:
      - APP_ENV=development
      - DEBUG=true
      - LOG_LEVEL=info
      - DATABASE_URL=postgresql+asyncpg://finuser:finpass@postgres:5432/financial_analyzer
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=${OPENAI_MODEL:-gpt-4}
      - CREWAI_VERBOSE=true
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - JWT_ALGORITHM=${JWT_ALGORITHM:-HS256}
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=${JWT_ACCESS_TOKEN_EXPIRE_MINUTES:-30}
      - JWT_REFRESH_TOKEN_EXPIRE_DAYS=${JWT_REFRESH_TOKEN_EXPIRE_DAYS:-7}
      - ADMIN_SEED_EMAIL=${ADMIN_SEED_EMAIL}
      - ADMIN_SEED_NAME=${ADMIN_SEED_NAME}
      - ADMIN_SEED_PASSWORD=${ADMIN_SEED_PASSWORD}
    expose:
      - "8000" # Only exposed to nginx, not host
    volumes:
      - ./backend/app:/app/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - fin-doc-network

  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: fin-doc-postgres
    environment:
      POSTGRES_USER: finuser
      POSTGRES_PASSWORD: finpass
      POSTGRES_DB: financial_analyzer
    ports:
      - "5431:5432" # Map host 5431 to container 5432
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U finuser -d financial_analyzer"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - fin-doc-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: fin-doc-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - fin-doc-network

volumes:
  postgres_data:
  redis_data:

networks:
  fin-doc-network:
    driver: bridge
```

### Step 6: Update Backend Dockerfile (Minor)

**Path**: `backend/Dockerfile`

- Ensure it uses `0.0.0.0` for host binding (already done)
- The existing Dockerfile is mostly compatible

## Environment Variables Required

Create a `.env` file in the root directory (or use existing `backend/.env`):

```bash
# OpenAI
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4

# JWT
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin Seed (optional)
ADMIN_SEED_EMAIL=admin@example.com
ADMIN_SEED_NAME=Admin User
ADMIN_SEED_PASSWORD=adminpassword
```

## Usage

### Start All Services

```bash
docker-compose up --build
```

### Access Points

- **Application**: http://localhost (nginx serves everything)
- **API Docs**: http://localhost/api/docs
- **Direct Backend**: Not exposed (use nginx proxy)
- **Direct Frontend**: Not exposed (use nginx proxy)
- **PostgreSQL**: localhost:5431 (for external tools)
- **Redis**: localhost:6379 (for external tools)

### Development Features

- **Hot Reload**: Both frontend and backend support code changes without restart
- **Volume Mounts**: Local code changes reflect immediately in containers
- **WebSocket HMR**: Vite hot module replacement works through nginx
- **Logs**: View all service logs in one terminal with `docker-compose logs -f`

## Migration from Existing Setup

The existing `backend/docker-compose.yml` can be:

1. **Option A**: Deleted (use root-level only)
2. **Option B**: Kept for backend-only development
3. **Option C**: Renamed to `docker-compose.backend-only.yml`

## Network Communication

| From               | To                  | URL                    |
| ------------------ | ------------------- | ---------------------- |
| Browser            | Nginx               | `http://localhost`     |
| Nginx              | Frontend            | `http://frontend:5174` |
| Nginx              | Backend             | `http://backend:8000`  |
| Frontend Container | Backend (via Nginx) | `/api/*`               |
| Backend Container  | PostgreSQL          | `postgres:5432`        |
| Backend Container  | Redis               | `redis:6379`           |

## Routing Rules

| Path                | Destination    | Example                                      |
| ------------------- | -------------- | -------------------------------------------- |
| `/`                 | Frontend index | `http://localhost/` → React app              |
| `/login`            | Frontend route | `http://localhost/login` → React router      |
| `/api/*`            | Backend API    | `http://localhost/api/health` → FastAPI      |
| `/api/docs`         | Swagger UI     | `http://localhost/api/docs` → API docs       |
| `/api/openapi.json` | OpenAPI schema | `http://localhost/api/openapi.json` → Schema |

## Notes

1. **Single Entry Point**: All traffic goes through nginx on port 80, simplifying CORS and SSL termination

2. **Frontend API Calls**: The frontend uses `VITE_API_BASE_URL=/api` which nginx routes to the backend

3. **WebSocket HMR**: Vite's hot module replacement works through nginx with proper upgrade headers

4. **Port Mapping**: PostgreSQL uses port 5431 on host to avoid conflicts with local PostgreSQL (if installed), but uses standard 5432 internally

5. **Hot Reload**: Both frontend and backend use volume mounts with polling/watch modes enabled for Docker compatibility

6. **Node Modules**: The frontend uses an anonymous volume for `node_modules` to prevent overwriting container's installed modules with host's empty directory

7. **Security**: Backend and frontend are not directly exposed to host, only accessible through nginx
