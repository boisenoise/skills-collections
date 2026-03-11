# Traceability & Verification (Criteria #16-#17, #22)

<!-- SCOPE: Story-Task alignment (#16), AC coverage (#17), and AC verify methods (#22). -->
<!-- DO NOT add here: Structural validation -> structural_validation.md, quality -> quality_validation.md -->

Detailed rules for Story-Task alignment, AC-Task coverage, and AC verification methods.

---

## Criterion #16: Story-Task Alignment

**Check:** Each Task implements part of Story statement (no orphan Tasks)

**Penalty:** MEDIUM (3 points)

**Rule:** Every Task must contribute to the Story goal. Tasks unrelated to Story statement are orphans. Skip when Story has no Tasks, or Story is Done/Canceled.

**Auto-fix actions:**
1. Extract Story Statement keywords (user, OAuth, log in, protected resources)
2. For EACH Task, check if title/description relates to Story keywords
3. IF Task misaligned: add TODO `_TODO: Verify this Task belongs to Story scope_` + warn user
4. IF multiple misaligned Tasks -> suggest splitting Story
5. Update Linear issue, add comment: "Story-Task alignment verified - [N] aligned, [M] warnings"

---

## Criterion #17: AC-Task Coverage

**Check:** Each Acceptance Criterion (AC) has at least one implementing Task

**Penalty:** MEDIUM (3 points)

**Rule:** Every AC must map to at least one Task. No ACs left without implementation. Skip when Story has no Tasks, or Story is Done/Canceled, or all ACs already have coverage notes.

### AC-Task Mapping Algorithm

1. Parse all Acceptance Criteria from Story
2. For EACH AC, find implementing Task(s) by keyword matching
3. Build coverage matrix:
   ```markdown
   ## AC-Task Coverage Matrix
   | AC | Task | Status |
   |----|------|--------|
   | 1 | T1 | Covered |
   | 2 | T2 | Covered |
   | 3 | - | MISSING |
   ```
4. **Coverage Quality Check** — for each AC->Task mapping, extract AC requirements:
   - **HTTP codes** (200, 201, 400, 401, 403, 404, 500)
   - **Error messages** ("Invalid token", "User not found", "Access denied")
   - **Performance criteria** (<200ms, <1s, 1000 req/sec)
   - **Timing constraints** (token expires in 1h, session timeout 30min)
5. **Scoring:**
   - **STRONG:** Task mentions all AC requirements (HTTP code + message + timing)
   - **WEAK:** Task exists but missing specific requirements
   - **MISSING:** No Task for AC
6. **Auto-fix:**
   - MISSING AC: add TODO to Story `_TODO: Add Task for AC #[N]: "[AC text]"_`
   - WEAK coverage: add TODO to Task `_TODO: Ensure AC requirement: [specific requirement]_`
7. Update coverage matrix with quality indicators:
   ```markdown
   | AC | Task | Status |
   |----|------|--------|
   | 1: Valid credentials -> 200 | T1 | STRONG (mentions 200, success flow) |
   | 2: Invalid token -> 401 | T2 | WEAK (mentions validation, no 401/message) |
   | 3: Timeout <200ms | - | MISSING |
   ```
8. Update Linear issue, add comment: "AC coverage - [N]/[M] ACs ([K] STRONG, [L] WEAK, [P] MISSING)"

---

## Criterion #22: AC Verify Methods

**Check:** Every Task AC has a `verify:` method; at least 1 non-inspect method per Task

**Penalty:** MEDIUM (3 points)

**Rule:** Each Task AC must specify how to verify it. Three method types:

| Type | When to use | Examples |
|------|------------|---------|
| `test` | Business logic, data transforms | Unit test, integration test |
| `command` | HTTP endpoints, CLI operations | `curl`, `npm run`, DB query |
| `inspect` | Config, docs, code structure | Code review, log check |

At least 1 AC per Task must use `test` or `command` (not all `inspect`). Skip when Task is Done/Canceled.

**Mapping heuristic:**
- HTTP endpoints, API routes → `command`
- DB operations, file I/O → `inspect`
- Business logic, calculations, transforms → `test`

**Auto-fix actions:**
1. For EACH Task, scan ACs for missing `verify:` line
2. Generate `verify:` method per mapping heuristic above
3. IF all ACs are `inspect` → convert the most testable one to `test` or `command`
4. Update Linear issue + add comment

---

**Version:** 2.0.0
**Last Updated:** 2026-02-03
