# build-and-test.md Template

<!-- SCOPE: build-and-test.md command template ONLY. Contains build/test steps, variable placeholders. -->
<!-- DO NOT add here: Generation workflow → ln-751-command-templates SKILL.md -->

Template for generating project-specific build and test command.

---

## Generated Command

```markdown
---
description: Full build and test verification
allowed-tools: Bash, Read
---

# Build and Test ({{PROJECT_NAME}})

Complete verification workflow: lint, build, test, Docker.

---

## Frontend Verification

```bash
cd {{FRONTEND_ROOT}}

# Lint
npm run lint

# Type check
npm run check

# Build
npm run build

# Tests
npm test -- --run
```

---

## Backend Verification

```bash
cd {{BACKEND_ROOT}}

# Build
dotnet build --no-restore

# Tests
dotnet test --no-build
```

---

## Docker Verification

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Wait for startup
sleep 30

# Health checks
curl -f http://localhost:{{FRONTEND_PORT}} || echo "Frontend: FAIL"
curl -f http://localhost:{{BACKEND_PORT}}/health || echo "Backend: FAIL"
```

---

## Full Pipeline (CI-style)

```bash
# Dependencies
cd {{FRONTEND_ROOT}} && npm ci
cd {{BACKEND_ROOT}} && dotnet restore

# Lint & Build
cd {{FRONTEND_ROOT}} && npm run lint && npm run build
cd {{BACKEND_ROOT}} && dotnet build

# Tests
cd {{FRONTEND_ROOT}} && npm test -- --run
cd {{BACKEND_ROOT}} && dotnet test

# Docker
docker-compose build
docker-compose up -d
```

---

## Report Checklist

- [ ] Frontend lint: PASS/FAIL
- [ ] Frontend build: PASS/FAIL
- [ ] Frontend tests: X passed, Y failed
- [ ] Backend build: PASS/FAIL
- [ ] Backend tests: X passed, Y failed
- [ ] Docker build: PASS/FAIL
- [ ] Health checks: PASS/FAIL

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
