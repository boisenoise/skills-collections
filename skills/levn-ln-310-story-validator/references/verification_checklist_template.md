# Story Verification Checklist (Template)

<!-- SCOPE: Verification checklist structure for ln-310-story-validator ONLY. Contains 17 criteria in 6 categories with penalty points. -->
<!-- DO NOT add here: validation implementation → SKILL.md, specific rules → individual validation files -->

General structure and category overview for ln-310-story-validator verification process.

**CRITICAL PRINCIPLE:** This skill ALWAYS auto-fixes all issues detected. Goal = 0 penalty points.

---

## Verification Categories (17 Criteria in 6 Groups)

| Category | Criteria | Penalty Range | Details |
|----------|----------|---------------|---------|
| **Structural** | #1-#4 | LOW-MEDIUM (1-3) | Story/Tasks structure, Statement, AC -> [structural_validation.md](structural_validation.md) |
| **Standards** | #5 | CRITICAL (10) | RFC/OWASP/REST/Security compliance -> [standards_validation.md](standards_validation.md) |
| **Solution** | #6 | HIGH (5) | Library versions -> [solution_validation.md](solution_validation.md) |
| **Workflow** | #7-#13 | LOW-MEDIUM (1-3) | Test Strategy, Docs integration, Size, Cleanup, YAGNI, KISS, Task order -> [workflow_validation.md](workflow_validation.md) |
| **Quality** | #14-#15 | MEDIUM-HIGH (3-5) | Documentation complete, Code quality -> [quality_validation.md](quality_validation.md) |
| **Traceability** | #16-#17 | MEDIUM (3) | Story-Task alignment, AC-Task coverage -> [traceability_validation.md](traceability_validation.md) |

---

## Penalty Points Summary

See [penalty_points.md](penalty_points.md) for full specification.

| Severity | Points | Description |
|----------|--------|-------------|
| CRITICAL | 10 | RFC/OWASP/security violations |
| HIGH | 5 | Outdated libraries, architecture |
| MEDIUM | 3 | Best practices violations |
| LOW | 1 | Structural/cosmetic issues |

**Goal:** 0 penalty points after auto-fix

---

## Execution Order (5 Phases)

**Detailed workflow:** See [SKILL.md Workflow Overview](../SKILL.md#workflow-overview)

**Quick summary:**
- **Phase 1:** Discovery & Loading (auto-discover config, load metadata)
- **Phase 2:** Research & Audit (domain extraction, ln-002 delegation, MCP research, penalty calculation)
- **Phase 3:** Audit Results & Fix Plan (show penalty table; IF Plan Mode: wait for approval)
- **Phase 4:** Auto-Fix (6 groups in order):
  1. Structural (#1-#4) — Story/Tasks template compliance
  2. Standards (#5) — RFC/OWASP compliance FIRST (before YAGNI/KISS!)
  3. Solution (#6) — Library versions
  4. Workflow (#7-#13) — Test strategy, docs, size, cleanup, YAGNI, KISS, task order
  5. Quality (#14-#15) — Documentation complete, hardcoded values
  6. Traceability (#16-#17) — Story-Task alignment, AC coverage (LAST)
- **Phase 5:** Approve & Notify (set Todo status, update kanban_board.md, Linear comment, tabular output)

---

## Mode Detection

| Mode | Behavior |
|------|----------|
| **Plan Mode** | Phase 1-2: audit, Phase 3: show results + WAIT, Phase 4-5: after approval |
| **Normal Mode** | Phase 1-5: automatic, no stopping |

---

## Quick Reference Matrix

| # | Criterion | Penalty | Evidence Required |
|---|-----------|---------|-------------------|
| 1 | Story follows template? | LOW (1) | Section list |
| 2 | All Tasks follow template? | LOW (1) | Task validation count |
| 3 | Clear Story statement? | LOW (1) | Quote statement |
| 4 | Testable AC? | MEDIUM (3) | AC count |
| 5 | Standards compliant (RFC/OWASP)? | CRITICAL (10) | Standards list + MCP result |
| 6 | Library versions latest? | HIGH (5) | Context7 result |
| 7 | Test Strategy present (empty)? | LOW (1) | Section exists (empty) |
| 8 | Docs integrated? | MEDIUM (3) | Integration proof |
| 9 | Size 3-8 Tasks? | MEDIUM (3) | Task count |
| 10 | No premature test tasks? | MEDIUM (3) | Search result |
| 11 | YAGNI? | MEDIUM (3) | Scope review |
| 12 | KISS? | MEDIUM (3) | Simplicity reason |
| 13 | Foundation-first task order? | MEDIUM (3) | Task order |
| 14 | Documentation complete? | HIGH (5) | All doc paths from ln-002 |
| 15 | No hardcoded values? | MEDIUM (3) | TODO placeholders |
| 16 | Story-Task alignment? | MEDIUM (3) | Alignment check result |
| 17 | AC-Task coverage? | MEDIUM (3) | Coverage matrix |

---

## Auto-Fix Hierarchy

**CRITICAL:** Standards Compliance (#5) checked BEFORE KISS/YAGNI (#11-#12).

See [workflow_validation.md Auto-Fix Hierarchy](workflow_validation.md#auto-fix-hierarchy-critical) for priority levels.

**Quick rule:** Standards (Level 1-2) override simplicity principles (Level 3).

---

## Evidence-Based Verification Protocol

**MANDATORY:** Before marking ANY criterion as complete:

1. **Answer Self-Audit Question** for that criterion
2. **Provide concrete evidence** (document path, MCP result, Linear update)
3. **Document in Linear comment** (NOT separate file)

**If evidence missing -> CANNOT mark complete -> MUST perform action first**

---

## Detailed Validation Rules

For detailed instructions and auto-fix actions:

1. **Structural (#1-#4)** -> See [structural_validation.md](structural_validation.md)
2. **Standards (#5)** -> See [standards_validation.md](standards_validation.md)
3. **Solution (#6)** -> See [solution_validation.md](solution_validation.md)
4. **Workflow (#7-#13)** -> See [workflow_validation.md](workflow_validation.md)
5. **Quality (#14-#15)** -> See [quality_validation.md](quality_validation.md)
6. **Traceability (#16-#17)** -> See [traceability_validation.md](traceability_validation.md)

---

## Post-Verification

**Result:** ALWAYS Approve -> Todo (after penalty points = 0)
- Story: Backlog -> Todo
- All child Tasks: Backlog -> Todo
- kanban_board.md: Updated with APPROVED marker
- Linear comment: Penalty Points table (Before -> 0 After), fixes, docs

> [!NOTE]
> No "Keep in Backlog" path exists - all issues auto-fixed before approval

> [!WARNING]
> Marking complete without documented evidence = INVALID verification

---

**Version:** 3.0.0
**Last Updated:** 2025-01-07
