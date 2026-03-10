# Plan Gate Criteria

Approval criteria for automatic plan evaluation by Lead. Each stage has binary checks — all must pass for auto-approval.

## Criteria Per Stage

### Stage 0: Task Planning (ln-300)

| # | Criterion | Check | Pass |
|---|-----------|-------|------|
| 1 | Task count | `1 <= tasks_planned <= 8` | In range |
| 2 | Task structure | Each task has `title`, `goal`, `estimate` | All present |
| 3 | Execution order | Foundation-First justification present | Stated |

### Stage 1: Validation (ln-310)

| # | Criterion | Check | Pass |
|---|-----------|-------|------|
| 1 | AC coverage | All Story ACs referenced in plan | All listed |
| 2 | Risk identification | At least 1 risk identified | >= 1 risk |
| 3 | Validation strategy | Approach stated (penalty audit, agent review, etc.) | Stated |

### Stage 2: Execution (ln-400)

| # | Criterion | Check | Pass |
|---|-----------|-------|------|
| 1 | Task approach | Each task has implementation approach | All present |
| 2 | File ownership | Primary files listed per task, shared files (types, config, utils) documented as shared | No undocumented overlaps |
| 3 | Test plan | Test approach stated (what to test, how) | Stated |

### Stage 3: Quality Gate (ln-500)

| # | Criterion | Check | Pass |
|---|-----------|-------|------|
| 1 | Audit scope | >= 3 audit dimensions listed | >= 3 |
| 2 | Test commands | Specific commands to run (lint, test, build) | Listed |
| 3 | Branch strategy | Merge/push approach stated | Stated |

## Evaluation Algorithm

```
FUNCTION criteria_pass(plan_json, stage):
  criteria = CRITERIA_TABLE[stage]
  failures = []

  FOR each criterion IN criteria:
    IF NOT check(criterion, plan_json):
      failures.append({criterion.name, criterion.check, "MISSING"})

  IF failures is empty:
    RETURN {approved: true}
  ELSE:
    feedback = format_failures(failures)
    RETURN {approved: false, feedback: feedback}
```

## Feedback Format (for revisions)

When plan fails criteria, Lead sends structured feedback:

```
Plan for Stage {N} needs revision:
- MISSING: {criterion_name} — expected: {check_description}
- MISSING: {criterion_name} — expected: {check_description}
Please revise and include the missing elements.
```

## Revision Limits

- Max 2 revisions per stage (3 total attempts: initial + 2 revisions)
- After limit reached: `story_state = "PAUSED"`, escalate to user
- Counter: `plan_revision_count[str(N)]` in `.pipeline/state.json` (string keys: `"0"`, `"1"`, `"2"`, `"3"`)

---
**Version:** 1.0.0
**Last Updated:** 2026-03-09
