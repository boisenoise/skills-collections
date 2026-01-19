# Test Documentation

**Last Updated:** {{DATE}}

<!-- SCOPE: Test organization structure and Story-Level Test Task Pattern ONLY. Contains test directories organization, test execution commands, quick navigation. -->
<!-- DO NOT add here: Test code → Test files, Story implementation → docs/tasks/kanban_board.md, Test strategy → Story test task descriptions -->

---

## Overview

This directory contains all tests for the project, following the **Story-Level Test Task Pattern** where tests are consolidated in the final Story test task (NOT scattered across implementation tasks).

**Test organization:**
- **E2E tests** (End-to-End) - 2-5 per Story - Priority ≥15 scenarios MUST be tested
- **Integration tests** - 3-8 per Story - Multi-component interactions
- **Unit tests** - 5-15 per Story - Individual component logic
- **Total**: 10-28 tests per Story (Value-Based Testing)

---

## Testing Philosophy

**Test YOUR code, not frameworks.** Focus on business logic and integration usage. Avoid testing database constraints, ORM internals, or framework validation.

**Risk-based testing:** Automate only Priority ≥15 scenarios (Business Impact × Probability). Test caps prevent bloat: 2-5 E2E, 3-8 Integration, 5-15 Unit (10-28 total per Story). No minimum limits - can be 0 if no high-priority scenarios exist.

**Rule of thumb:** If deleting your code wouldn't fail the test, you're testing someone else's code.

👉 **Full strategy:** See [docs/reference/guides/testing-strategy.md](../docs/reference/guides/testing-strategy.md)

---

## Test Structure

```
tests/
├── e2e/                        # End-to-End tests (2-5 per Story)
│   ├── auth/
│   ├── user-flows/
│   └── critical-paths/
├── integration/                # Integration tests (3-8 per Story)
│   ├── api/
│   ├── database/
│   └── services/
├── unit/                       # Unit tests (5-15 per Story)
│   ├── components/
│   ├── utils/
│   └── services/
└── manual/                     # Manual test scripts (bash/curl)
    ├── config.sh               # Shared configuration
    ├── README.md               # Manual tests documentation
    ├── test-all.sh             # Run all test suites
    ├── results/                # Test outputs (in .gitignore)
    └── NN-feature/             # Test suites by Story
        ├── samples/            # Input files
        ├── expected/           # Expected outputs (REQUIRED)
        └── test-*.sh           # Test scripts
```

---

## Manual Testing

Manual test scripts in `tests/manual/` follow strict testing principles:

**Design Principles:**
1. **Fail-Fast** - Tests return 1 immediately on failure (no soft warnings)
2. **Expected-Based** - Compare actual vs expected files (`diff`), not heuristics
3. **Results Stored** - All outputs in `results/` for debugging

**Templates (2 types):**
- `TEMPLATE-api-endpoint.sh` - For direct API calls (no async jobs)
- `TEMPLATE-document-format.sh` - For document processing (upload → poll → download)

**Run manual tests:**
```bash
cd tests/manual
./test-all.sh                   # Run ALL manual test suites
./NN-feature/test-*.sh          # Run specific test suite
```

**See:** ln-512-manual-tester for full documentation of Test Design Principles.

---

## Story-Level Test Task Pattern

**Rule**: All tests (E2E/Integration/Unit) are written in the **final Story test task** (created by ln-510-test-planner after manual testing).

**Why**:
- **Single source of truth**: All Story tests in one place
- **Atomic completion**: Story Done when all tests pass
- **No scattered tests**: NOT in implementation tasks
- **Regression prevention**: Test suite runs before Story marked Done

**Workflow**:
1. Implementation tasks completed → Manual testing → Bugs fixed
2. ln-510-test-planner creates Story Finalizer test task
3. ln-404-test-executor implements all tests (E2E/Integration/Unit) in final task
4. All tests pass → Story marked Done

---

## Test Execution

**Run all tests:**
```bash
npm test
```

**Run specific test suites:**
```bash
npm run test:unit           # Unit tests only
npm run test:integration    # Integration tests only
npm run test:e2e            # E2E tests only
```

**Watch mode (development):**
```bash
npm run test:watch
```

---

## Quick Navigation

- **Testing Strategy**: [docs/reference/guides/testing-strategy.md](../docs/reference/guides/testing-strategy.md) - Philosophy, risk-based strategy, what to test
- **Story test tasks**: [docs/tasks/kanban_board.md](../docs/tasks/kanban_board.md) - Story test task tracking
- **Story-Level Pattern**: [docs/tasks/README.md](../docs/tasks/README.md) - Full pattern explanation
- **Test guidelines**: [docs/reference/guides/](../docs/reference/guides/) - Additional testing best practices

---

## Maintenance

**Update Triggers**:
- When adding new test directories or test suites
- When changing test execution commands
- When modifying Story-Level Test Task Pattern workflow

**Verification**:
- All test directories exist (e2e/, integration/, unit/, manual/)
- `tests/manual/results/` is in `.gitignore`
- Test execution commands work correctly
- SCOPE tags correctly define test documentation boundaries

**Last Updated**: {{DATE}}
