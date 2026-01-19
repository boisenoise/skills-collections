# refresh_context.md Template

Template for generating project-specific context refresh command.

---

## Generated Command

```markdown
---
description: Restore project context after memory loss or compression
allowed-tools: Read, Glob, Grep
---

# Refresh Context ({{PROJECT_NAME}})

## Project Profile

| Property | Value |
|----------|-------|
| **Project** | {{PROJECT_NAME}} |
| **Tech Stack** | {{TECH_STACK}} |
| **Frontend** | {{FRONTEND_ROOT}} |
| **Backend** | {{BACKEND_ROOT}} |

---

## Minimal Anchor (ALWAYS load first)

Read `CLAUDE.md` for architecture, commands, and conventions.

---

## Detailed Deep-Dive (ON DEMAND)

### Frontend Context
- `{{FRONTEND_ROOT}}/src/App.tsx` — Entry point
- `{{FRONTEND_ROOT}}/src/pages/` — Page components
- `{{FRONTEND_ROOT}}/src/components/` — Shared components
- `{{FRONTEND_ROOT}}/src/hooks/` — Custom hooks
- `{{FRONTEND_ROOT}}/src/api/` — API client

### Backend Context
- `{{BACKEND_ROOT}}/Program.cs` — Startup configuration
- `{{BACKEND_ROOT}}/Controllers/` — API endpoints
- `{{BACKEND_ROOT}}/Services/` — Business logic
- `{{BACKEND_ROOT}}/Data/` — Database context

---

## Development URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:{{FRONTEND_PORT}} |
| Backend API | http://localhost:{{BACKEND_PORT}}/api |
| Swagger | http://localhost:{{BACKEND_PORT}}/swagger |

---

## Quick Commands

| Action | Command |
|--------|---------|
| Start Frontend | `cd {{FRONTEND_ROOT}} && npm run dev` |
| Start Backend | `cd {{BACKEND_ROOT}} && dotnet watch run` |
| Run Tests | `npm test && dotnet test` |
| Docker Up | `docker-compose up -d` |

---

## Output After Refresh

Report:
1. **Status:** "Context refreshed ({{PROJECT_NAME}})"
2. **Files Read:** List key files loaded
3. **Next Steps:** Based on current task

---

**Generated:** {{TIMESTAMP}}
```

---

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{PROJECT_NAME}}` | Project name | "kehai-os" |
| `{{TECH_STACK}}` | Stack summary | "React + .NET + PostgreSQL" |
| `{{FRONTEND_ROOT}}` | Frontend path | "src/frontend" |
| `{{BACKEND_ROOT}}` | Backend path | "src/Kehai.Api" |
| `{{FRONTEND_PORT}}` | Frontend port | "3000" |
| `{{BACKEND_PORT}}` | Backend port | "5000" |
| `{{TIMESTAMP}}` | Generation time | "2026-01-10" |

---

**Version:** 2.0.0
**Last Updated:** 2026-01-10
