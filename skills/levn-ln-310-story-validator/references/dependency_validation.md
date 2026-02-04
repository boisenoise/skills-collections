# Dependency Validation (Criteria #18-#19)

<!-- SCOPE: Story/Task dependency validation criteria #18-#19 ONLY. Contains forward dependency detection, sequential completability checks. -->
<!-- DO NOT add here: Structural validation → structural_validation.md, workflow → workflow_validation.md -->

Detailed rules for Story and Task independence validation (no forward dependencies).

---

## Criterion #18: Story Dependencies (Within-Epic)

**Check:** No Story depends on FUTURE Stories (only previous Stories allowed)

**Penalty:** CRITICAL (10 points)

**What it checks:**
- Story N can be completed using only Stories 1 to N-1
- No forward references to Stories N+1, N+2, etc.
- Each Story builds on previous Stories' outputs
- Stories are independently executable in sequence

---

## Examples #18

**GOOD (Sequential Dependency):**
```markdown
## Epic 1: User Authentication

Story 1.1: User Registration
- Depends On: None
- Status: Can complete independently

Story 1.2: User Login
- Depends On: Story 1.1 (uses user table from 1.1)
- Status: Can complete using only 1.1 output

Story 1.3: Token Refresh
- Depends On: Story 1.2 (uses auth flow from 1.2)
- Status: Can complete using only 1.1 + 1.2 outputs
```

**BAD (Forward Dependency):**
```markdown
## Epic 1: User Authentication

Story 1.1: User Login
- Depends On: Story 1.3 (requires token validation from 1.3)  <- FORWARD!
- Status: BLOCKED by future Story

Story 1.2: Password Reset
- Depends On: Story 1.4 (requires email service from 1.4)  <- FORWARD!
- Status: BLOCKED by future Story

Story 1.3: Token Validation
- Depends On: None
```

**Why Forward Dependencies Are Critical:**
- Break sequential execution flow
- Create circular dependencies
- Prevent incremental delivery
- Violate INVEST Independence principle

---

## Auto-fix Actions #18

1. **Load all Stories in Epic:**
   - Query Linear: `list_issues(project=Epic.id, label="user-story")`
   - Sort by Story number (US001, US002, US003...)

2. **For EACH Story, parse Dependencies section:**
   - Extract "Depends On" field
   - Parse Story references (US001, US002, Story 1.1, Story 1.2)
   - Normalize to Story numbers (1.1, 1.2, 1.3)

3. **Check for forward dependencies:**
   ```
   FOR Story N in Epic:
     FOR each dependency D in Story N.dependencies:
       IF D.number > N.number:
         FLAG as CRITICAL violation
         ADD penalty: 10 points
   ```

4. **Build dependency graph:**
   ```markdown
   ## Dependency Graph
   Story 1.1 → (none)
   Story 1.2 → Story 1.1 ✅
   Story 1.3 → Story 1.5 ❌ FORWARD!
   Story 1.4 → Story 1.2, Story 1.3 ⚠️ (depends on 1.3 which is blocked)
   ```

5. **Suggest fixes:**
   - IF Story N depends on Story N+K:
     - **Option A:** Reorder Stories (move Story N+K before Story N)
     - **Option B:** Split Epic (move dependent Stories to separate Epic)
     - **Option C:** Remove dependency (make Stories independent)

6. **Update Linear:**
   - Add comment to Story N: "⚠️ CRITICAL: Forward dependency on Story N+K detected. Cannot execute until dependency resolved."
   - Add comment to Epic: "Epic has forward dependencies. Stories cannot execute sequentially."

7. **Warn user:**
   ```
   CRITICAL: Epic has forward dependencies
   - Story 1.2 depends on Story 1.4
   - Story 1.3 depends on Story 1.5

   Recommended actions:
   1. Reorder Stories to resolve dependencies
   2. Split Epic if dependencies are complex
   3. Make Stories more independent
   ```

---

## Criterion #19: Task Dependencies (Within-Story)

**Check:** No Task depends on FUTURE Tasks (only previous Tasks allowed)

**Penalty:** MEDIUM (3 points)

**What it checks:**
- Task N can be completed using only Tasks 1 to N-1
- No forward references to Tasks N+1, N+2, etc.
- Each Task builds on previous Tasks' outputs
- Tasks follow Foundation-First order (DB → Service → API → UI)

---

## Examples #19

**GOOD (Sequential Dependency):**
```markdown
## Implementation Tasks

Task 1: Create Users table
- Depends On: None
- Output: Users schema in database

Task 2: Implement UserRepository
- Depends On: Task 1 (uses Users table)
- Output: Data access layer

Task 3: Implement UserService
- Depends On: Task 2 (uses UserRepository)
- Output: Business logic layer

Task 4: Implement /api/users endpoint
- Depends On: Task 3 (uses UserService)
- Output: REST API
```

**BAD (Forward Dependency):**
```markdown
## Implementation Tasks

Task 1: Implement /api/users endpoint
- Depends On: Task 3 (requires UserService)  <- FORWARD!

Task 2: Implement UserRepository
- Depends On: Task 4 (requires validation from Task 4)  <- FORWARD!

Task 3: Implement UserService
- Depends On: Task 2 (uses UserRepository)  <- OK

Task 4: Add validation middleware
- Depends On: None
```

**Why Task Forward Dependencies Matter:**
- Break Foundation-First execution order
- Prevent task-by-task implementation
- Create implementation blockers
- Violate sequential work pattern

---

## Auto-fix Actions #19

1. **Load all Tasks in Story:**
   - Query Linear: `list_issues(parentId=Story.id)`
   - Filter: implementation tasks only (exclude test tasks)
   - Sort by Task number (T-001, T-002, T-003...)

2. **For EACH Task, parse dependencies:**
   - Search Task description for keywords: "requires", "depends on", "needs", "uses output from"
   - Extract Task references (T-001, T-002, Task 1, Task 2)
   - Normalize to Task numbers (1, 2, 3)

3. **Check for forward dependencies:**
   ```
   FOR Task N in Story:
     Parse Task N description
     Extract dependency keywords
     FOR each dependency D:
       IF D references Task M where M > N:
         FLAG as MEDIUM violation
         ADD penalty: 3 points
   ```

4. **Check Foundation-First order:**
   - Database tasks (T-001 to T-002)
   - Service tasks (T-003 to T-004)
   - API tasks (T-005 to T-006)
   - IF Task N (API) comes before Task M (Database):
     - FLAG as order violation
     - Suggest reordering

5. **Suggest fixes:**
   - IF Task N depends on Task N+K:
     - **Option A:** Reorder Tasks (move Task N+K before Task N)
     - **Option B:** Remove dependency (refactor to use only previous Tasks)
     - **Option C:** Split Task N (extract dependent part to new Task after N+K)

6. **Update Linear:**
   - Add TODO to Task N: `_TODO: Task depends on future Task N+K. Reorder or refactor._`
   - Update Implementation Plan with correct order

7. **Build corrected order:**
   ```markdown
   ## Corrected Task Order

   Before (with forward dependencies):
   1. Task API endpoint (depends on Task 3)
   2. Task Repository
   3. Task Service (depends on Task 2)

   After (Foundation-First):
   1. Task Repository (no dependencies)
   2. Task Service (uses Task 1)
   3. Task API endpoint (uses Task 2)
   ```

---

## Dependency Detection Patterns

**Story Dependencies (Criterion #18):**

Search in Story "Dependencies" section:
```markdown
## Dependencies
**Depends On:**
- Story 1.3: Token validation  <- Extract "1.3"
- US005: User profile  <- Extract "005" → Story 1.5
```

Keywords to detect implicit dependencies:
- "requires Story N"
- "depends on Story N"
- "needs Story N to be completed"
- "blocked by Story N"
- "waits for Story N"

**Task Dependencies (Criterion #19):**

Search in Task description (all sections):
```markdown
## Context
Requires Task 3 to generate tokens  <- FORWARD!

## Implementation Plan
Phase 1: Uses output from Task 4  <- FORWARD!

## Technical Approach
Depends on validation middleware from Task 5  <- FORWARD!
```

Keywords to detect:
- "requires Task N"
- "depends on Task N"
- "needs Task N output"
- "uses Task N result"
- "waits for Task N"

---

## Execution Order

**CRITICAL:** Dependency checks run in Group 6 (after Workflow fixes, before Traceability)

**Rationale:**
- Criterion #18 (Story Dependencies) requires all Stories loaded (Phase 2)
- Criterion #19 (Task Dependencies) requires Task order finalized (criterion #13 completed)
- Running earlier = checking against incomplete/unordered data

**Sequence:**
```
Phase 4 Groups 1-5 complete:
  - Structural (#1-#4) → Stories/Tasks structured
  - Standards (#5) → Compliance verified
  - Solution (#6) → Libraries updated
  - Workflow (#7-#13) → Task order finalized (Foundation-First)
  - Quality (#14-#15) → Documentation complete

→ Group 6: Dependencies (#18-#19) runs
  - Check Story forward dependencies
  - Check Task forward dependencies

→ Group 7: Traceability (#16-#17) runs
  - Verify final alignment and coverage
```

---

## Skip Fix When

- Story/Task in Done/Canceled status
- Story/Task older than 30 days (legacy, don't touch)
- Epic has only 1 Story (no dependencies possible)
- Story has only 1 Task (no dependencies possible)

---

## Execution Notes

**Sequential Dependency:**
- Criteria #18-#19 depend on #1-#15 being completed first
- Must run AFTER Task order finalized (#13)
- Must run BEFORE Traceability (#16-#17)

**Linear Updates:**
- Each criterion auto-fix updates Linear issue once
- Add comment: "Dependency validation: [N] forward dependencies detected, [M] fixed"

**User Warnings:**
- Forward dependencies = CRITICAL for Stories, MEDIUM for Tasks
- Always suggest reordering as primary fix
- Provide clear before/after examples

---

## Integration with Other Criteria

**Criterion #13 (Task Order):**
- #13 checks Foundation-First LAYERS (DB → Service → API)
- #19 checks NO FORWARD DEPENDENCIES (Task N → Task N+1)
- Both work together to ensure correct task sequence

**Criterion #16 (Story-Task Alignment):**
- #16 checks Tasks align with Story statement
- #18 checks Stories align sequentially in Epic
- Both ensure traceability at different levels

**Example:**
```
Criterion #13: "Tasks are ordered DB → Service → API" ✅
Criterion #19: "Task 2 (Service) doesn't depend on Task 4 (future)" ✅

Result: Tasks can execute sequentially without blockers
```

---

**Version:** 1.0.0 (NEW: Story/Task dependency validation per BMAD Method best practices)
**Last Updated:** 2026-02-03
