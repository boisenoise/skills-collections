# ui-testing.md Template

Template for generating Playwright UI testing command.

**Condition:** Generated only if Playwright detected (playwright.config.ts or @playwright/test in deps)

---

## Generated Command

```markdown
---
description: Run Playwright UI tests with screenshots and traces
allowed-tools: Bash, Read
---

# UI Testing ({{PROJECT_NAME}})

Run Playwright end-to-end tests with visual feedback.

---

## Prerequisites

Ensure services are running:
```bash
docker-compose up -d
cd {{FRONTEND_ROOT}} && npm run dev &
cd {{BACKEND_ROOT}} && dotnet watch run &
```

---

## Run Tests

### All Tests
```bash
cd {{FRONTEND_ROOT}}
npx playwright test
```

### Specific Test File
```bash
npx playwright test tests/auth.spec.ts
```

### Headed Mode (Visual)
```bash
npx playwright test --headed
```

### Debug Mode
```bash
npx playwright test --debug
```

---

## Test Report

### Open Last Report
```bash
npx playwright show-report
```

### Generate HTML Report
```bash
npx playwright test --reporter=html
```

---

## Screenshots & Traces

### Take Screenshot on Failure
Already configured in playwright.config.ts

### View Trace
```bash
npx playwright show-trace test-results/*/trace.zip
```

### Record New Trace
```bash
npx playwright test --trace on
```

---

## Update Snapshots

If visual tests fail due to intentional changes:
```bash
npx playwright test --update-snapshots
```

---

## Common Issues

### Browser Not Installed
```bash
npx playwright install
```

### Port Conflict
Ensure {{FRONTEND_PORT}} and {{BACKEND_PORT}} are available.

### Timeout Issues
Increase timeout in playwright.config.ts or use:
```bash
npx playwright test --timeout=60000
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
