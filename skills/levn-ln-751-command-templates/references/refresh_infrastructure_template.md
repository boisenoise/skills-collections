# refresh_infrastructure.md Template

Template for generating project-specific infrastructure restart command.

---

## Generated Command

```markdown
---
description: Full infrastructure refresh (stop -> start -> verify)
allowed-tools: Bash, Read
---

# Refresh Infrastructure ({{PROJECT_NAME}})

## Quick Restart

### All Services (Docker)
```bash
docker-compose down && docker-compose up -d
```

### Frontend Only
```bash
cd {{FRONTEND_ROOT}} && npm run dev
```

### Backend Only
```bash
cd {{BACKEND_ROOT}} && dotnet watch run
```

---

## Full Reset (Clean Restart)

```bash
# Stop everything
docker-compose down -v

# Clear caches
cd {{FRONTEND_ROOT}} && rm -rf node_modules/.cache dist
cd {{BACKEND_ROOT}} && dotnet clean

# Reinstall dependencies
cd {{FRONTEND_ROOT}} && npm ci
cd {{BACKEND_ROOT}} && dotnet restore

# Start fresh
docker-compose up -d
```

---

## Database Operations

### Reset Database
```bash
docker-compose down -v postgres
docker-compose up -d postgres
sleep 5
dotnet ef database update --project {{BACKEND_ROOT}}
```

### View Logs
```bash
docker-compose logs -f postgres
```

---

## Service Health Check

```bash
# Docker containers
docker-compose ps

# Frontend
curl -s http://localhost:{{FRONTEND_PORT}} > /dev/null && echo "Frontend: OK" || echo "Frontend: FAIL"

# Backend
curl -s http://localhost:{{BACKEND_PORT}}/health && echo "Backend: OK" || echo "Backend: FAIL"

# Database
docker-compose exec postgres pg_isready && echo "Database: OK" || echo "Database: FAIL"
```

---

## Port Conflicts

### Find Process on Port (Windows)
```bash
netstat -ano | findstr :{{FRONTEND_PORT}}
netstat -ano | findstr :{{BACKEND_PORT}}
```

### Find Process on Port (Linux/Mac)
```bash
lsof -i :{{FRONTEND_PORT}}
lsof -i :{{BACKEND_PORT}}
```

---

## Environment Setup

```bash
# Copy example if missing
cp .env.example .env

# Required variables:
# DATABASE_URL=Host=localhost;Database={{PROJECT_NAME}};Username=postgres;Password=postgres
# JWT_SECRET=your-secret-key
```

---

**Generated:** {{TIMESTAMP}}
```

---

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{PROJECT_NAME}}` | Project name | "kehai-os" |
| `{{FRONTEND_ROOT}}` | Frontend path | "src/frontend" |
| `{{BACKEND_ROOT}}` | Backend path | "src/Kehai.Api" |
| `{{FRONTEND_PORT}}` | Frontend port | "3000" |
| `{{BACKEND_PORT}}` | Backend port | "5000" |
| `{{TIMESTAMP}}` | Generation time | "2026-01-10" |

---

**Version:** 2.0.0
**Last Updated:** 2026-01-10
