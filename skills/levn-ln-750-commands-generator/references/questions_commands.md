# Questions: Command Validation

<!-- SCOPE: Command file validation questions ONLY. Contains per-command questions, auto-discovery rules. -->
<!-- DO NOT add here: Generation workflow → ln-750-commands-generator SKILL.md, templates → ln-751-command-templates -->

Validation questions for generated .claude/commands/ files.

---

## Table of Contents

| Document | Questions | Auto-Discovery | Priority | Line |
|----------|-----------|----------------|----------|------|
| refresh_context.md | 3 | Full | High | 20 |
| refresh_infrastructure.md | 3 | Full | High | 55 |
| build-and-test.md | 3 | Full | High | 90 |
| ui-testing.md | 2 | Conditional | Medium | 125 |
| deploy.md | 2 | Conditional | Medium | 150 |
| database-ops.md | 2 | Conditional | Medium | 175 |

---

<!-- DOCUMENT_START: refresh_context -->
## refresh_context.md

Core command for restoring project context after memory loss.

<!-- QUESTION_START: 1 -->
### Question 1: Does the command reference CLAUDE.md?

**Requirement:** Must include instruction to read CLAUDE.md as minimal anchor.

**Validation:** Check for "CLAUDE.md" mention in Minimal Anchor section.

**Auto-Discovery:** Check file exists in .claude/commands/refresh_context.md
<!-- QUESTION_END: 1 -->

<!-- QUESTION_START: 2 -->
### Question 2: Are project paths correctly substituted?

**Requirement:** {{FRONTEND_ROOT}} and {{BACKEND_ROOT}} must be replaced with actual paths.

**Validation:** No `{{` placeholders remaining in generated file.

**Auto-Discovery:** Grep for `\{\{` in generated file - should return 0 matches.
<!-- QUESTION_END: 2 -->

<!-- QUESTION_START: 3 -->
### Question 3: Are development URLs correct?

**Requirement:** Frontend and backend URLs must use correct ports.

**Validation:** URLs match actual running services.

**Auto-Discovery:** Parse URLs and verify ports match vite.config/launchSettings.
<!-- QUESTION_END: 3 -->

<!-- DOCUMENT_END: refresh_context -->

---

<!-- DOCUMENT_START: refresh_infrastructure -->
## refresh_infrastructure.md

Core command for restarting development services.

<!-- QUESTION_START: 1 -->
### Question 1: Does the command include docker-compose operations?

**Requirement:** Must have docker-compose down/up commands.

**Validation:** Check for docker-compose commands in generated file.

**Auto-Discovery:** Grep for "docker-compose" in generated file.
<!-- QUESTION_END: 1 -->

<!-- QUESTION_START: 2 -->
### Question 2: Are health check URLs correct?

**Requirement:** Health check URLs must use correct ports.

**Validation:** curl commands use correct {{FRONTEND_PORT}} and {{BACKEND_PORT}}.

**Auto-Discovery:** Parse curl commands and verify port numbers.
<!-- QUESTION_END: 2 -->

<!-- QUESTION_START: 3 -->
### Question 3: Are all placeholders substituted?

**Requirement:** No {{VAR}} placeholders remaining.

**Validation:** No `{{` in generated file.

**Auto-Discovery:** Grep for `\{\{` - should return 0 matches.
<!-- QUESTION_END: 3 -->

<!-- DOCUMENT_END: refresh_infrastructure -->

---

<!-- DOCUMENT_START: build-and-test -->
## build-and-test.md

Core command for full build and test verification.

<!-- QUESTION_START: 1 -->
### Question 1: Does the command include frontend build steps?

**Requirement:** Must have npm run lint, npm run build, npm test.

**Validation:** Check for npm commands in Frontend section.

**Auto-Discovery:** Grep for "npm run build" in generated file.
<!-- QUESTION_END: 1 -->

<!-- QUESTION_START: 2 -->
### Question 2: Does the command include backend build steps?

**Requirement:** Must have dotnet build and dotnet test.

**Validation:** Check for dotnet commands in Backend section.

**Auto-Discovery:** Grep for "dotnet build" in generated file.
<!-- QUESTION_END: 2 -->

<!-- QUESTION_START: 3 -->
### Question 3: Does the command include Docker verification?

**Requirement:** Must have docker-compose build and health checks.

**Validation:** Check for Docker section with curl commands.

**Auto-Discovery:** Grep for "docker-compose build" in generated file.
<!-- QUESTION_END: 3 -->

<!-- DOCUMENT_END: build-and-test -->

---

<!-- DOCUMENT_START: ui-testing -->
## ui-testing.md

Optional command for Playwright UI tests.

<!-- QUESTION_START: 1 -->
### Question 1: Is Playwright configured in project?

**Requirement:** Only generate if playwright.config.ts exists or @playwright/test in deps.

**Validation:** Check for Playwright configuration.

**Auto-Discovery:** Glob for playwright.config.ts or check package.json devDeps.
<!-- QUESTION_END: 1 -->

<!-- QUESTION_START: 2 -->
### Question 2: Does the command include test commands?

**Requirement:** Must have npx playwright test commands.

**Validation:** Check for Playwright CLI commands.

**Auto-Discovery:** Grep for "npx playwright" in generated file.
<!-- QUESTION_END: 2 -->

<!-- DOCUMENT_END: ui-testing -->

---

<!-- DOCUMENT_START: deploy -->
## deploy.md

Optional command for deployment workflow.

<!-- QUESTION_START: 1 -->
### Question 1: Is CI/CD configured in project?

**Requirement:** Only generate if .github/workflows/ or Dockerfile exists.

**Validation:** Check for CI/CD configuration.

**Auto-Discovery:** Glob for .github/workflows/*.yml or Dockerfile.
<!-- QUESTION_END: 1 -->

<!-- QUESTION_START: 2 -->
### Question 2: Does the command include production build steps?

**Requirement:** Must have production build commands for frontend and backend.

**Validation:** Check for Release configuration builds.

**Auto-Discovery:** Grep for "npm run build" and "dotnet publish" in generated file.
<!-- QUESTION_END: 2 -->

<!-- DOCUMENT_END: deploy -->

---

<!-- DOCUMENT_START: database-ops -->
## database-ops.md

Optional command for database operations.

<!-- QUESTION_START: 1 -->
### Question 1: Is database configured in project?

**Requirement:** Only generate if PostgreSQL in docker-compose or EF Core detected.

**Validation:** Check for database configuration.

**Auto-Discovery:** Grep docker-compose.yml for postgres or check for EF Core packages.
<!-- QUESTION_END: 1 -->

<!-- QUESTION_START: 2 -->
### Question 2: Does the command include migration commands?

**Requirement:** Must have dotnet ef database update command.

**Validation:** Check for EF Core CLI commands.

**Auto-Discovery:** Grep for "dotnet ef" in generated file.
<!-- QUESTION_END: 2 -->

<!-- DOCUMENT_END: database-ops -->

---

**Version:** 2.0.0
**Last Updated:** 2026-01-10
