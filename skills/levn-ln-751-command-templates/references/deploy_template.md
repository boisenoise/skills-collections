# deploy.md Template

<!-- SCOPE: deploy.md command template ONLY. Contains deployment steps, conditional generation. -->
<!-- DO NOT add here: Generation workflow → ln-751-command-templates SKILL.md -->

Template for generating deployment workflow command.

**Condition:** Generated only if CI/CD config detected (.github/workflows/, Dockerfile, etc.)

---

## Generated Command

```markdown
---
description: Build and deploy application
allowed-tools: Bash, Read
---

# Deploy ({{PROJECT_NAME}})

Production build and deployment workflow.

---

## Pre-Deploy Checklist

- [ ] All tests pass (`/build-and-test`)
- [ ] No uncommitted changes (`git status`)
- [ ] On correct branch (`git branch`)
- [ ] Version updated if needed

---

## Build for Production

### Frontend Build
```bash
cd {{FRONTEND_ROOT}}
npm ci
npm run build
```

### Backend Build
```bash
cd {{BACKEND_ROOT}}
dotnet restore
dotnet publish -c Release -o ./publish
```

---

## Docker Build

### Build Images
```bash
docker-compose -f docker-compose.prod.yml build
```

### Tag Images
```bash
docker tag {{PROJECT_NAME}}-frontend:latest registry/{{PROJECT_NAME}}-frontend:v1.0.0
docker tag {{PROJECT_NAME}}-backend:latest registry/{{PROJECT_NAME}}-backend:v1.0.0
```

### Push Images
```bash
docker push registry/{{PROJECT_NAME}}-frontend:v1.0.0
docker push registry/{{PROJECT_NAME}}-backend:v1.0.0
```

---

## Deploy Steps

### Option 1: Docker Compose (Single Server)
```bash
ssh user@server "cd /app && docker-compose pull && docker-compose up -d"
```

### Option 2: Kubernetes
```bash
kubectl apply -f k8s/
kubectl rollout status deployment/{{PROJECT_NAME}}
```

### Option 3: GitHub Actions
Push to main branch triggers automatic deployment via .github/workflows/deploy.yml

---

## Post-Deploy Verification

### Health Check
```bash
curl -f https://your-domain.com/health
curl -f https://your-domain.com/api/health
```

### Smoke Tests
```bash
# Run critical path tests against production
npx playwright test tests/smoke.spec.ts --config=playwright.prod.config.ts
```

---

## Rollback

### Docker Compose
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

### Kubernetes
```bash
kubectl rollout undo deployment/{{PROJECT_NAME}}
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
| `{{TIMESTAMP}}` | Generation time | "2026-01-10" |

---

**Version:** 2.0.0
**Last Updated:** 2026-01-10
