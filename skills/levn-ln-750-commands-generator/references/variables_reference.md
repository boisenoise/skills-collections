# Variables Reference

<!-- SCOPE: Command template variable definitions ONLY. Contains variable names, sources, example values. -->
<!-- DO NOT add here: Generation workflow → ln-750-commands-generator SKILL.md -->

Complete list of variables extracted by ln-750 for command generation.

---

## Core Variables

| Variable | Description | Source | Example |
|----------|-------------|--------|---------|
| `{{PROJECT_NAME}}` | Project name | package.json name or .csproj | "kehai-os" |
| `{{PROJECT_DESCRIPTION}}` | Project description | package.json description | "Task management app" |
| `{{TECH_STACK}}` | Stack summary | Auto-detected | "React + .NET + PostgreSQL" |
| `{{TIMESTAMP}}` | Generation time | Current datetime | "2026-01-10" |

---

## Path Variables

| Variable | Description | Detection | Example |
|----------|-------------|-----------|---------|
| `{{FRONTEND_ROOT}}` | Frontend source path | package.json location | "src/frontend" |
| `{{BACKEND_ROOT}}` | Backend source path | .csproj location | "src/MyApp.Api" |

---

## URL & Port Variables

| Variable | Description | Source | Example |
|----------|-------------|--------|---------|
| `{{FRONTEND_PORT}}` | Frontend dev port | vite.config.ts server.port | "3000" |
| `{{BACKEND_PORT}}` | Backend API port | launchSettings.json | "5000" |
| `{{DEV_URL}}` | Frontend URL | Computed | "http://localhost:3000" |
| `{{API_URL}}` | Backend API URL | Computed | "http://localhost:5000" |
| `{{SWAGGER_URL}}` | Swagger URL | Computed | "http://localhost:5000/swagger" |

---

## Framework Variables

| Variable | Description | Source | Example |
|----------|-------------|--------|---------|
| `{{FRONTEND_FRAMEWORK}}` | Frontend framework | package.json deps | "React 19" |
| `{{BACKEND_FRAMEWORK}}` | Backend framework | .csproj SDK | "ASP.NET Core 10" |
| `{{DATABASE}}` | Database type | docker-compose.yml | "PostgreSQL 17" |

---

## Detection Logic

### Frontend Detection

```yaml
Files to check:
  - vite.config.ts / vite.config.js
  - webpack.config.js
  - next.config.js
  - package.json

Framework detection:
  - "react" in dependencies → React
  - "vue" in dependencies → Vue
  - "angular" in dependencies → Angular
  - "svelte" in dependencies → Svelte

Port detection:
  - vite.config: server.port
  - package.json: scripts.dev --port
  - Default: 3000
```

### Backend Detection

```yaml
.NET detection:
  - *.csproj with Sdk="Microsoft.NET.Sdk.Web"
  - launchSettings.json for ports

Node detection:
  - express/fastify/nestjs in package.json

Python detection:
  - requirements.txt with flask/fastapi/django

Port detection:
  - .NET: launchSettings.json applicationUrl
  - Node: PORT env or package.json scripts
  - Python: uvicorn --port or flask run
  - Default: 5000
```

### Database Detection

```yaml
Docker detection:
  - docker-compose.yml services: postgres, mysql, mongodb

Connection strings:
  - appsettings.json ConnectionStrings
  - .env DATABASE_URL

Default ports:
  - PostgreSQL: 5432
  - MySQL: 3306
  - MongoDB: 27017
```

### Optional Features Detection

```yaml
Playwright:
  - playwright.config.ts exists
  - @playwright/test in devDependencies

CI/CD:
  - .github/workflows/*.yml exists
  - azure-pipelines.yml exists
  - Dockerfile exists

Database migrations:
  - dotnet ef in global tools
  - prisma in devDependencies
  - alembic in requirements.txt
```

---

**Version:** 2.0.0
**Last Updated:** 2026-01-10
