# Traceability Validation (Criteria #16-#17)

<!-- SCOPE: Story-Task alignment and AC coverage criteria #16-#17 ONLY. Contains orphan task detection, AC-Task mapping. -->
<!-- DO NOT add here: Structural validation → structural_validation.md, quality → quality_validation.md -->

Detailed rules for Story-Task alignment and AC-Task coverage verification.

---

## Criterion #16: Story-Task Alignment

**Check:** Each Task implements part of Story statement (no orphan Tasks)

**Penalty:** MEDIUM (3 points)

**What it checks:**
- Every Task contributes to the Story goal
- No Tasks that don't relate to Story statement
- Tasks together cover the full Story scope

---

## Examples #16

**GOOD (Aligned):**
```markdown
## Story Statement
As a user, I want to log in with OAuth so that I can access protected resources.

## Implementation Tasks

1. [Task] Implement OAuth 2.0 token endpoint - US-123-T1
   -> Implements "log in with OAuth"

2. [Task] Add token validation middleware - US-123-T2
   -> Implements "access protected resources"

3. [Task] Create protected route example - US-123-T3
   -> Implements "access protected resources"
```

**BAD (Misaligned):**
```markdown
## Story Statement
As a user, I want to log in with OAuth so that I can access protected resources.

## Implementation Tasks

1. [Task] Implement OAuth endpoint - US-123-T1 (OK)
2. [Task] Add user profile page - US-123-T2 <- NOT in Story scope!
3. [Task] Implement rate limiting - US-123-T3 <- NOT in Story scope!
```

---

## Auto-fix Actions #16

1. Extract Story Statement keywords (user, OAuth, log in, protected resources)
2. For EACH Task, check if title/description relates to Story keywords
3. IF Task misaligned:
   - Add TODO to Task: `_TODO: Verify this Task belongs to Story scope_`
   - Warn user: "Task [name] may not align with Story statement"
4. IF multiple misaligned Tasks -> Suggest splitting Story
5. Update Linear issue via `mcp__linear-server__update_issue`
6. Add comment: "Story-Task alignment verified - [N] Tasks aligned, [M] warnings"

---

## Criterion #17: AC-Task Coverage

**Check:** Each Acceptance Criterion (AC) has at least one implementing Task

**Penalty:** MEDIUM (3 points)

**What it checks:**
- Every AC maps to at least one Task
- No ACs left without implementation
- Coverage matrix is complete

---

## Examples #17

**GOOD (Full Coverage):**
```markdown
## Acceptance Criteria
1. User can enter credentials and click Login
2. System validates credentials against OAuth provider
3. User receives error message for invalid credentials
4. User is redirected to dashboard after successful login

## Implementation Tasks

1. [Task] Login form UI - US-123-T1
   -> Covers AC #1

2. [Task] OAuth validation service - US-123-T2
   -> Covers AC #2, #3

3. [Task] Dashboard redirect logic - US-123-T3
   -> Covers AC #4

## AC-Task Coverage Matrix
| AC | Task | Status |
|----|------|--------|
| 1 | T1 | Covered |
| 2 | T2 | Covered |
| 3 | T2 | Covered |
| 4 | T3 | Covered |
```

**BAD (Missing Coverage):**
```markdown
## Acceptance Criteria
1. User can enter credentials and click Login
2. System validates credentials against OAuth provider
3. User receives error message for invalid credentials  <- NO TASK!
4. User is redirected to dashboard after successful login

## Implementation Tasks

1. [Task] Login form UI - US-123-T1 (AC #1)
2. [Task] OAuth validation - US-123-T2 (AC #2)
3. [Task] Dashboard redirect - US-123-T3 (AC #4)
   (AC #3 has no implementing Task!)
```

---

## Auto-fix Actions #17

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
4. IF AC uncovered:
   - Add TODO to Story: `_TODO: Add Task for AC #[N]: "[AC text]"_`
   - Suggest Task title: "Implement [AC summary]"
5. Update Linear issue via `mcp__linear-server__update_issue`
6. Add comment: "AC coverage verified - [N]/[M] ACs covered, [K] missing"

---

## Coverage Matrix Format

**Auto-generated in Technical Notes:**

```markdown
## AC-Task Traceability

| AC # | Acceptance Criterion | Implementing Task(s) | Status |
|------|---------------------|---------------------|--------|
| 1 | User can enter credentials | T1: Login form UI | Covered |
| 2 | System validates credentials | T2: OAuth validation | Covered |
| 3 | Error message for invalid creds | T2: OAuth validation | Covered |
| 4 | Redirect to dashboard | T3: Dashboard redirect | Covered |

**Coverage:** 4/4 ACs (100%)
```

---

## Execution Order

**CRITICAL:** Traceability checks run LAST (after all other fixes)

**Rationale:**
- #16 Story-Task Alignment requires final Task list (after #9 consolidation)
- #17 AC-Task Coverage requires final AC list (after #4 fixes)
- Running earlier = checking against incomplete data

**Sequence:**
```
Phase 4 Groups 1-5 complete -> All Tasks/ACs finalized
-> Group 6: Traceability (#16-#17) runs
-> Verifies final alignment and coverage
```

---

## Skip Fix When

- Story has no Tasks yet (validation stage)
- Story in Done/Canceled status
- All ACs already have coverage notes

---

## Execution Notes

**Sequential Dependency:**
- Criteria #16-#17 depend on #1-#15 being completed first
- Must run AFTER Task consolidation (#9)
- Must run AFTER AC verification (#4)

**Linear Updates:**
- Each criterion auto-fix updates Linear issue once
- Add comment: "Traceability verified - Story alignment OK, AC coverage [N]%"

---

**Version:** 1.0.0
**Last Updated:** 2025-01-07
