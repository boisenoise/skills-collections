# Penalty Points System

Detailed specification for the quantitative Story/Tasks quality assessment.

---

## Overview

**Goal:** Reach 0 penalty points after validation and auto-fix.

**Principle:** Every violation has a cost. Higher severity = higher cost. All violations must be fixed.

---

## Severity Levels

| Severity | Points | Description | Examples |
|----------|--------|-------------|----------|
| **CRITICAL** | 10 | Security, RFC, OWASP violations | Missing auth, SQL injection risk, RFC non-compliance |
| **HIGH** | 5 | Architecture, outdated libraries | Wrong patterns, Express v4.17 vs v4.19 |
| **MEDIUM** | 3 | Best practices violations | No edge cases in AC, YAGNI violation |
| **LOW** | 1 | Structural, cosmetic issues | Missing section, wrong order |

---

## Criteria Penalty Mapping

| # | Criterion | Severity | Points | Category |
|---|-----------|----------|--------|----------|
| 1 | Story Structure | LOW | 1 | Structural |
| 2 | Tasks Structure | LOW | 1 | Structural |
| 3 | Story Statement | LOW | 1 | Structural |
| 4 | Acceptance Criteria | MEDIUM | 3 | Structural |
| 5 | Standards Compliance | CRITICAL | 10 | Standards |
| 6 | Library & Version | HIGH | 5 | Solution |
| 7 | Test Strategy | LOW | 1 | Workflow |
| 8 | Documentation Integration | MEDIUM | 3 | Workflow |
| 9 | Story Size | MEDIUM | 3 | Workflow |
| 10 | Test Task Cleanup | MEDIUM | 3 | Workflow |
| 11 | YAGNI | MEDIUM | 3 | Workflow |
| 12 | KISS | MEDIUM | 3 | Workflow |
| 13 | Task Order | MEDIUM | 3 | Workflow |
| 14 | Documentation Complete | HIGH | 5 | Quality |
| 15 | Code Quality Basics | MEDIUM | 3 | Quality |
| 16 | Story-Task Alignment | MEDIUM | 3 | Traceability |
| 17 | AC-Task Coverage | MEDIUM | 3 | Traceability |

**Maximum possible penalty:** 50 points (if all criteria violated)

### Category Summary

| Category | Criteria | Total Points |
|----------|----------|--------------|
| Structural | #1-#4 | 6 |
| Standards | #5 | 10 |
| Solution | #6 | 5 |
| Workflow | #7-#13 | 19 |
| Quality | #14-#15 | 8 |
| Traceability | #16-#17 | 6 |
| **TOTAL** | **17** | **50** |

---

## Calculation Rules

### Per-Criterion Calculation

```
FOR each criterion (1-17):
  IF violation detected:
    penalty_points += criterion.severity_points
  ELSE:
    penalty_points += 0 (criterion passed)
```

### Multiple Violations per Criterion

Some criteria can have multiple violations:

| Criterion | Multiple Violations | Calculation |
|-----------|---------------------|-------------|
| #2 Tasks Structure | Per Task | 1 point * violated_tasks_count |
| #4 Acceptance Criteria | Per missing AC | 3 points * missing_ac_count (max 3x = 9) |
| #9 Story Size | Per issue | 3 points * size_issues_count |
| #16 Story-Task Alignment | Per misaligned Task | 3 points * misaligned_tasks_count (max 3x = 9) |
| #17 AC-Task Coverage | Per uncovered AC | 3 points * uncovered_ac_count (max 3x = 9) |
| Others | Single | Fixed points per criterion |

**Examples:**
- Story has 5 Tasks, 2 violate structure -> 1 * 2 = 2 points
- AC missing 2 edge cases -> 3 * 2 = 6 points (capped at 9)
- 2 Tasks don't align with Story -> 3 * 2 = 6 points (capped at 9)
- 1 AC has no implementing Task -> 3 * 1 = 3 points

---

## Penalty Points Report Format

### Phase 3 Output (Audit Results)

```
PENALTY POINTS AUDIT
====================

| # | Criterion               | Severity | Points | Issue                          |
|---|-------------------------|----------|--------|--------------------------------|
| 4 | Acceptance Criteria     | MEDIUM   | 3      | Missing edge case for empty    |
| 5 | Standards Compliance    | CRITICAL | 10     | No RFC 7231/OWASP compliance   |
| 6 | Library & Version       | HIGH     | 5      | Express v4.17 -> v4.19         |
|17 | AC-Task Coverage        | MEDIUM   | 3      | AC "Error 401" has no Task     |

TOTAL: 21 penalty points

FIX PLAN:
- #4: Add Given/When/Then for empty input case
- #5: Add RFC 7231 error response + OWASP checklist
- #6: Update Express version in Technical Notes
- #17: Add TODO for missing token validation Task
```

### Phase 5 Output (Final Report)

```
VALIDATION COMPLETE
===================

PENALTY POINTS: 21 -> 0

| # | Criterion               | Before | After | Fixed |
|---|-------------------------|--------|-------|-------|
| 4 | Acceptance Criteria     | 3      | 0     | Yes   |
| 5 | Standards Compliance    | 10     | 0     | Yes   |
| 6 | Library & Version       | 5      | 0     | Yes   |
|17 | AC-Task Coverage        | 3      | 0     | Yes   |

TOTAL: 21 -> 0 (100% fixed)

Story approved: Backlog -> Todo
```

---

## Integration with Workflow

### Phase 2: Calculation

1. Evaluate each criterion
2. Detect violations
3. Assign penalty points
4. Calculate total
5. Build fix plan

### Phase 3: Display

1. Show Penalty Points table
2. Show total
3. Show fix plan
4. IF Plan Mode: wait for approval

### Phase 4: Zeroing

1. Execute fix for each violation
2. Zero out criterion penalty
3. Update running total
4. Confirm all fixed

### Phase 5: Verification

1. Verify total = 0
2. Report Before -> After
3. Approve Story

---

## Edge Cases

### Zero Violations

```
PENALTY POINTS AUDIT
====================

No violations detected.

TOTAL: 0 penalty points

Story approved: Backlog -> Todo
```

### Maximum Violations

If total > 30 points, add warning:

```
WARNING: High violation count (42 points)
Consider Story scope review before approval.
```

---

**Version:** 2.0.0
**Last Updated:** 2025-01-07
