# Verification Rules by Document Type

<!-- SCOPE: Per-document verification patterns for semantic content audit. Contains detection methods, evidence collection, common issues per document type. -->

Detailed verification patterns for each project document type.

## General Verification Patterns

### Path Verification

```bash
# Check if path exists
ls -la "$PROJECT_ROOT/$path" 2>&1

# If not exists → OUTDATED_PATH finding
```

### Version Verification

```bash
# Node.js
grep '"$package"' package.json | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+'

# Python
grep '$package' requirements.txt | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+'

# Go
grep '$module' go.mod | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+'
```

### Import Pattern Verification

```bash
# Check if component A imports from component B
grep -rn "import.*$B" "$A_folder/"
```

---

## 1. CLAUDE.md

### Expected Scope
Project instructions for Claude Code: repository overview, key concepts, workflows, important details.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| "Files in `src/utils/`" | `ls src/utils/` | OUTDATED_PATH |
| "Run `npm run build`" | Check package.json scripts | MISSING_COMMAND |
| "Config in `config/`" | `ls config/` | OUTDATED_PATH |
| "Main entry `src/index.ts`" | `ls src/index.ts` | OUTDATED_PATH |

### Common Issues
- References to moved/renamed folders
- Outdated npm scripts
- Wrong file extensions (.js vs .ts)
- References to removed features

---

## 2. docs/README.md

### Expected Scope
Documentation hub: navigation to all docs, brief descriptions, structure overview.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| Link `[X](path/to/x.md)` | `ls docs/path/to/x.md` | BROKEN_LINK |
| "Contains N documents" | `find docs/ -name "*.md" \| wc -l` | WRONG_COUNT |
| Folder structure diagram | `ls -la docs/` | STRUCTURE_MISMATCH |

### Common Issues
- Broken internal links after reorganization
- Outdated folder structure diagrams
- Links to removed documents

---

## 3. docs/project/architecture.md

### Expected Scope
System architecture: C4 diagrams, component interactions, layer separation, data flow.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| "3-tier: Controller->Service->Repository" | Check import patterns (see below) | BEHAVIOR_MISMATCH |
| "Components: Auth, Users, Orders" | `ls src/` for folders | MISSING_COMPONENT |
| "Database: PostgreSQL" | Check docker-compose, .env, ORM config | WRONG_TECH |
| "Cache layer with Redis" | Grep for redis imports | MISSING_COMPONENT |

### Layer Verification Pattern

```bash
# If docs say "Controller -> Service -> Repository" (no direct Controller->Repository)

# Controllers should import Services
grep -rn "import.*Service" src/controllers/  # Should have results

# Controllers should NOT import Repositories directly
grep -rn "import.*Repository" src/controllers/  # Should be EMPTY

# Services should import Repositories
grep -rn "import.*Repository" src/services/  # Should have results
```

**If Controller imports Repository directly:** BEHAVIOR_MISMATCH (layer violation)

### Common Issues
- Architecture diagrams show ideal, not actual
- Removed components still documented
- Layer violations not reflected in docs
- Missing new components added after docs written

---

## 4. docs/project/tech_stack.md

### Expected Scope
Technologies, versions, rationale for choices.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| "Node.js 20.x" | Check .nvmrc, package.json engines | WRONG_VERSION |
| "Express 4.18" | `grep express package.json` | WRONG_VERSION |
| "PostgreSQL 15" | Check docker-compose, CI config | WRONG_VERSION |
| "Uses TypeScript" | Check for tsconfig.json | WRONG_TECH |

### Version Extraction Commands

```bash
# Node.js packages
cat package.json | grep -A1 '"express"' | tail -1 | tr -d ' ",'

# Python packages
grep 'django' requirements.txt

# Docker images
grep 'postgres:' docker-compose.yml
```

### Common Issues
- Documented versions lag behind actual (updated deps, forgot docs)
- Removed dependencies still listed
- New dependencies not documented
- Version ranges in docs vs exact in lockfile

---

## 5. docs/project/api_spec.md

### Expected Scope
API endpoints, request/response schemas, authentication, error codes.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| "GET /api/users" | Grep route definitions | MISSING_ENDPOINT |
| "Returns {id, name, email}" | Check controller response | WRONG_SCHEMA |
| "Requires Bearer token" | Check auth middleware usage | WRONG_AUTH |
| "Returns 404 if not found" | Check error handling | MISSING_ERROR_CODE |

### Endpoint Verification Pattern

```bash
# Express routes
grep -rn "get.*\/api\/users\|router.get.*users" src/routes/

# Fastify routes
grep -rn "fastify.get.*\/api\/users" src/

# NestJS controllers
grep -rn "@Get.*users" src/
```

### Response Schema Verification

```bash
# Find controller method, check what it returns
grep -A20 "getUsers\|findAll" src/controllers/UserController.ts
```

### Common Issues
- Removed endpoints still documented
- New endpoints not in spec
- Response schema changed (added/removed fields)
- Authentication requirements changed
- Error codes not matching implementation

---

## 6. docs/project/database_schema.md

### Expected Scope
Database tables, columns, relationships, indexes.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| "Table: users" | Check migrations or schema file | MISSING_TABLE |
| "Column: users.email" | Check schema definition | MISSING_COLUMN |
| "FK: orders.user_id -> users.id" | Check migration/schema | MISSING_RELATION |
| "Index on users.email" | Check migration/schema | MISSING_INDEX |

### Schema Verification by ORM

```bash
# Prisma
grep -A50 "model User" prisma/schema.prisma

# TypeORM
grep -rn "@Entity.*User\|@Column" src/entities/User.ts

# Sequelize
grep -A30 "User.init" src/models/User.js

# Raw migrations
ls migrations/ | head -20
grep -l "CREATE TABLE users" migrations/
```

### Common Issues
- Schema docs lag behind migrations
- Removed columns still documented
- New tables/columns not in docs
- Relationship changes not reflected

---

## 7. docs/project/requirements.md

### Expected Scope
Functional requirements (FR-XXX), user stories, acceptance criteria.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| "FR-001: User can register" | Search for registration feature | UNIMPLEMENTED |
| "FR-005: Export to CSV" | Search for export functionality | UNIMPLEMENTED |
| "MoSCoW: Must-have" for feature X | Check if feature exists | PRIORITY_MISMATCH |

### Feature Verification Pattern

```bash
# Search for feature keywords in codebase
grep -rn "register\|signup\|createUser" src/

# Check for specific functionality
grep -rn "export.*csv\|toCSV\|downloadCSV" src/
```

### Common Issues
- Planned features documented but never implemented
- Implemented features not in requirements
- Changed scope not reflected (features removed/modified)
- Stale MoSCoW priorities

---

## 8. docs/project/design_guidelines.md

### Expected Scope
Design system: colors, typography, components, spacing, accessibility.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| "Primary color: #3B82F6" | Check CSS variables/theme | WRONG_VALUE |
| "Button component" | Check component exists | MISSING_COMPONENT |
| "Tailwind CSS" | Check tailwind.config.js | WRONG_TECH |
| "WCAG 2.1 AA" | Check for a11y patterns | MISSING_FEATURE |

### Style Verification Pattern

```bash
# CSS variables
grep -rn "primary\|--color-primary" src/**/*.css

# Tailwind config
cat tailwind.config.js | grep -A20 "colors"

# Component existence
ls src/components/Button* 2>/dev/null
```

### Common Issues
- Colors changed in theme but not docs
- Removed components still documented
- New design tokens not documented

---

## 9. docs/project/runbook.md

### Expected Scope
Setup, deployment, troubleshooting, environment variables.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| "Run `npm install`" | Check package.json exists | INVALID_COMMAND |
| "Set DATABASE_URL env" | Grep for env var usage | UNUSED_ENV_VAR |
| "Docker: `docker-compose up`" | Check docker-compose.yml exists | MISSING_FILE |
| "Port 3000" | Check actual port in code | WRONG_VALUE |

### Command Verification

```bash
# Check if npm script exists
grep '"start"' package.json

# Check if env var is used
grep -rn "DATABASE_URL\|process.env.DATABASE_URL" src/

# Check if docker-compose exists
ls docker-compose.yml docker-compose.yaml 2>/dev/null
```

### Common Issues
- Outdated setup instructions
- Removed environment variables still documented
- Changed ports/URLs
- Missing new setup steps

---

## 10. docs/principles.md

### Expected Scope
Development principles, coding standards, architectural decisions.

### Verification Checks

| Claim Type | How to Verify | Finding if False |
|------------|---------------|------------------|
| "SOLID principles" | Sample code for patterns | PRINCIPLE_VIOLATION |
| "No magic numbers" | Grep for hardcoded values | PRINCIPLE_VIOLATION |
| "Error handling with try/catch" | Check error patterns | INCONSISTENT_PATTERN |

### Principle Verification (Sampling)

```bash
# Sample 3-5 files to check principle adherence
# Example: "No magic numbers"
grep -rn "[^0-9][0-9]\{3,\}[^0-9]" src/ | head -10  # Large numbers in code

# Example: "Consistent error handling"
grep -rn "catch\|try {" src/ | wc -l  # Should be significant if claimed
```

### Common Issues
- Stated principles not followed in practice
- New patterns emerged but not documented
- Outdated standards (deprecated practices)

---

## Severity Guidelines

| Severity | Criteria | Examples |
|----------|----------|----------|
| **HIGH** | Misleading information, causes failures | Wrong API endpoints, missing required setup steps |
| **MEDIUM** | Outdated but not breaking | Old version numbers, removed optional features |
| **LOW** | Minor inconsistencies | Typos in paths, formatting differences |

---
**Version:** 1.0.0
**Last Updated:** 2026-01-28
