# Transformation Plan Template

Template for generating bootstrap transformation plans.

---

## Template Structure

```markdown
# Bootstrap Transformation Plan

**Project:** {{PROJECT_NAME}}
**Generated:** {{DATE}}
**Estimated Duration:** {{DURATION}}

---

## Source Analysis

### Detected Stack

| Layer | Current | Target |
|-------|---------|--------|
| Frontend | {{FRONTEND_CURRENT}} | {{FRONTEND_TARGET}} |
| Backend | {{BACKEND_CURRENT}} | {{BACKEND_TARGET}} |
| Database | {{DATABASE}} | {{DATABASE}} |
| ORM | {{ORM_CURRENT}} | {{ORM_TARGET}} |

### Current Structure

```
{{CURRENT_STRUCTURE}}
```

### Target Structure

```
{{TARGET_STRUCTURE}}
```

---

## Transformation Steps

### Step 1: Dependencies (ln-710)

**Upgrades Required:**
{{#each DEPENDENCY_UPGRADES}}
- {{package}}: {{current}} -> {{target}}
{{/each}}

**Breaking Changes:**
{{#each BREAKING_CHANGES}}
- {{package}}: {{description}}
  - Migration: {{migration_link}}
{{/each}}

**Estimated Impact:** {{DEPENDENCY_IMPACT}}

---

### Step 2: Structure Migration (ln-720)

**Frontend Restructuring:**
{{#each FRONTEND_CHANGES}}
- {{action}}: {{source}} -> {{destination}}
{{/each}}

**Backend Generation:**
- Create: {{BACKEND_PROJECTS}}
- Template: Clean Architecture (.NET)
- MockData migration from: {{ORM_CURRENT}}

**Files to Delete:**
{{#each DELETE_FILES}}
- {{file}} ({{reason}})
{{/each}}

---

### Step 3: DevOps Setup (ln-730)

**Docker:**
- [ ] Dockerfile.frontend (multi-stage, nginx)
- [ ] Dockerfile.backend (.NET SDK)
- [ ] docker-compose.yml ({{SERVICES}})
- [ ] .dockerignore

**CI/CD:**
- Provider: {{CICD_PROVIDER}}
- Workflows:
  - ci.yml (build, test, lint)
  - deploy.yml (optional)

**Environment:**
- [ ] .env.example
- [ ] .env.development
- [ ] .env.production (template)

---

### Step 4: Quality Setup (ln-740)

**Linters:**
- Frontend: ESLint ({{ESLINT_CONFIG}}) + Prettier
- Backend: {{BACKEND_LINTER}}

**Pre-commit Hooks:**
- Husky + lint-staged
- Commitlint (conventional commits)

**Test Infrastructure:**
- Frontend: {{FRONTEND_TEST_RUNNER}}
- Backend: {{BACKEND_TEST_RUNNER}}

---

### Step 5: Commands Generation (ln-750)

**Commands to Generate:**
{{#each COMMANDS}}
- {{name}}.md - {{description}}
{{/each}}

**Template Variables:**
- PROJECT_NAME: {{PROJECT_NAME}}
- FRONTEND_ROOT: {{FRONTEND_ROOT}}
- BACKEND_ROOT: {{BACKEND_ROOT}}
- DEV_URL: {{DEV_URL}}

---

### Step 6: Security Setup (ln-760)

**Scans:**
- [ ] Secret detection (hardcoded keys)
- [ ] Dependency audit (npm audit / dotnet)
- [ ] SAST configuration

**Generated Files:**
- SECURITY.md
- .gitignore updates
- .env.example (secrets template)

---

### Step 7: Crosscutting (ln-770)

**Logging:**
- Library: {{LOGGING_LIBRARY}}
- Format: JSON structured
- Levels: Debug (dev), Information (prod)

**Error Handling:**
- GlobalExceptionMiddleware
- ErrorBoundary (React)
- Standardized error response

**CORS:**
- Development: localhost origins
- Production: env-based

**Health Checks:**
- /health - basic
- /health/ready - with dependencies
- /health/live - liveness probe

**API Documentation:**
- Library: {{API_DOCS_LIBRARY}}
- Path: {{API_DOCS_PATH}}

---

### Step 8: Verification (ln-780)

**Build Verification:**
- [ ] Frontend: npm run build
- [ ] Backend: dotnet build

**Test Execution:**
- [ ] Frontend: {{FRONTEND_TEST_COMMAND}}
- [ ] Backend: {{BACKEND_TEST_COMMAND}}

**Container Launch:**
- [ ] docker-compose build
- [ ] docker-compose up -d
- [ ] Wait 30s for startup

**Health Checks:**
- [ ] {{FRONTEND_URL}} -> 200 OK
- [ ] {{BACKEND_URL}}/health -> 200 OK
- [ ] {{BACKEND_URL}}/swagger -> 200 OK

---

## Estimated Changes

| Category | Created | Modified | Deleted |
|----------|---------|----------|---------|
| Frontend | {{FC}} | {{FM}} | {{FD}} |
| Backend | {{BC}} | {{BM}} | {{BD}} |
| DevOps | {{DC}} | {{DM}} | {{DD}} |
| Config | {{CC}} | {{CM}} | {{CD}} |
| **Total** | **{{TC}}** | **{{TM}}** | **{{TD}}** |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
{{#each RISKS}}
| {{description}} | {{probability}} | {{impact}} | {{mitigation}} |
{{/each}}

---

## Rollback Plan

If bootstrap fails:
1. Git reset to pre-bootstrap commit
2. Restore original package.json
3. Remove generated .NET projects
4. Remove Docker files

**Backup created at:** {{BACKUP_PATH}}
```

---

## Variable Reference

| Variable | Source | Example |
|----------|--------|---------|
| PROJECT_NAME | package.json name or folder | kehai-os |
| FRONTEND_CURRENT | Detection | React 18 + Vite |
| BACKEND_CURRENT | Detection | Express + Drizzle |
| BACKEND_TARGET | User preference | .NET 10 |
| DATABASE | Detection | PostgreSQL 17 |
| CICD_PROVIDER | User preference | github |
| LOGGING_LIBRARY | Stack-based | Serilog |
| API_DOCS_LIBRARY | Stack-based | Swashbuckle |

---

## Example: Filled Template

```markdown
# Bootstrap Transformation Plan

**Project:** kehai-os
**Generated:** 2026-01-10
**Estimated Duration:** 25-30 minutes

---

## Source Analysis

### Detected Stack

| Layer | Current | Target |
|-------|---------|--------|
| Frontend | React 18 + Vite 5 | React 19 + Vite 6 |
| Backend | Express + Drizzle | .NET 10 + EF Core |
| Database | PostgreSQL 17 | PostgreSQL 17 |
| ORM | Drizzle | Entity Framework Core |

### Current Structure

```
kehai-os/
├── client/
│   └── src/
│       └── App.tsx (monolithic)
├── server/
│   └── index.ts
├── shared/
│   └── schema.ts
└── package.json
```

### Target Structure

```
kehai-os/
├── src/
│   ├── frontend/
│   │   └── src/
│   │       ├── components/
│   │       ├── pages/
│   │       ├── hooks/
│   │       └── lib/
│   ├── Kehai.Api/
│   ├── Kehai.Domain/
│   ├── Kehai.Services/
│   └── Kehai.Repositories/
├── docker-compose.yml
└── .github/workflows/
```
```

---

**Version:** 1.0.0
**Last Updated:** 2026-01-10
