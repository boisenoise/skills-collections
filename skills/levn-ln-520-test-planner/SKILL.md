---
name: ln-520-test-planner
description: "Orchestrates test planning pipeline: research, manual testing, automated test planning. Use when Story needs comprehensive test coverage planning."
license: MIT
---

> **Paths:** File paths (`shared/`, `references/`, `../ln-*`) are relative to skills repo root. If not found at CWD, locate this SKILL.md directory and go up one level for repo root. If `shared/` is missing, fetch files via WebFetch from `https://raw.githubusercontent.com/levnikolaevich/claude-code-skills/master/skills/{path}`.

# Test Planning Orchestrator

Coordinates the complete test planning pipeline for a Story by delegating to specialized workers.

## Inputs

| Input | Required | Source | Description |
|-------|----------|--------|-------------|
| `storyId` | Yes | args, git branch, kanban, user | Story to process |
| `--simplified` | No | args | Skip research (ln-521) and manual testing (ln-522). Run only auto-test planning (ln-523). Used in fast-track mode. |

**Resolution:** Story Resolution Chain.
**Status filter:** To Review

## Purpose & Scope
- **Orchestrate** test planning: research → manual testing → automated test planning
- **Delegate** to workers: ln-521-test-researcher, ln-522-manual-tester, ln-523-auto-test-planner
- **No direct work** — only coordination and delegation via Skill tool
- **Called by** ln-500-story-quality-gate after regression tests pass

## When to Use

This skill should be used when:
- **Invoked by ln-500-story-quality-gate** after quality checks pass
- All implementation tasks in Story are Done
- Need complete test planning (research + manual + auto)

**Prerequisites:**
- All implementation Tasks in Story status = Done
- Regression tests passed (ln-513)
- Code quality checked (ln-511)

## Pipeline Overview

```
ln-520-test-planner (Orchestrator)
    │
    ├─→ ln-521-test-researcher
    │     └─→ Posts "## Test Research: {Feature}" comment
    │
    ├─→ ln-522-manual-tester
    │     └─→ Creates tests/manual/ scripts + "## Manual Testing Results" comment
    │
    └─→ ln-523-auto-test-planner
          └─→ Creates test task in Linear via ln-301/ln-302
```

## Workflow

### Phase 0: Resolve Inputs

**MANDATORY READ:** Load `shared/references/input_resolution_pattern.md`

1. **Resolve storyId:** Run Story Resolution Chain per guide (status filter: [To Review]).

### Phase 1: Discovery

1) Auto-discover Team ID from `docs/tasks/kanban_board.md`
2) Validate Story ID

### Phase 2: Research Delegation

> **Simplified mode gate:**
> - IF `--simplified` flag AND research comment already exists on Story: Skip Phase 2 (research). Proceed to Phase 4.
> - IF `--simplified` flag AND no research comment: Skip Phase 2. Proceed to Phase 4 (ln-523 will generate minimal inline research).

1) **Check if research exists:**
   - Search Linear comments for "## Test Research:" header
   - If found → skip to Phase 3

2) **If no research:**
   - **Use Skill tool to invoke `ln-521-test-researcher`**
   - Pass: Story ID
   - Wait for completion
   - Verify research comment created

### Phase 3: Manual Testing Delegation

> **Simplified mode gate:**
> - IF `--simplified` flag: Skip Phase 3 (manual testing). Proceed to Phase 4.

1) **Check if manual testing done:**
   - Search Linear comments for "## Manual Testing Results" header
   - If found with all AC passed → skip to Phase 4

2) **If manual testing needed:**
   - **Use Skill tool to invoke `ln-522-manual-tester`**
   - Pass: Story ID
   - Wait for completion
   - Verify results comment created

3) **If any AC failed:**
   - Stop pipeline
   - Report to ln-500: "Manual testing failed, Story needs fixes"

### Phase 4: Auto Test Planning Delegation

1) **Invoke auto test planner:**
   - **Use Skill tool to invoke `ln-523-auto-test-planner`**
   - Pass: Story ID
   - Wait for completion

2) **Verify results:**
   - Test task created in Linear (or updated if existed)
   - Return task URL to ln-500

### Phase 5: Report to Caller

1) Return summary to ln-500:
   - Research: completed / skipped (existed)
   - Manual testing: passed / failed
   - Test task: created / updated + URL

## Worker Invocation (MANDATORY)

> **CRITICAL:** All delegations use Agent tool with `subagent_type: "general-purpose"` for context isolation.

| Phase | Worker | Purpose |
|-------|--------|---------|
| 2 | ln-521-test-researcher | Research real-world problems |
| 3 | ln-522-manual-tester | Manual AC testing via bash scripts |
| 4 | ln-523-auto-test-planner | Plan E2E/Integration/Unit tests |

**Prompt template:**
```
Agent(description: "[Phase N] test planning via ln-52X",
     prompt: "Execute test planning worker.

Step 1: Invoke worker:
  Skill(skill: \"ln-52X-{worker}\")

CONTEXT:
Story: {storyId}",
     subagent_type: "general-purpose")
```

**Anti-Patterns:**
- ❌ Direct Skill tool invocation without Agent wrapper
- ❌ Running web searches directly (delegate to ln-521)
- ❌ Creating bash test scripts directly (delegate to ln-522)
- ❌ Creating test tasks directly (delegate to ln-523)
- ❌ Skipping any phase without justification

## Critical Rules

- **No direct work:** Orchestrator only delegates, never executes tasks itself
- **Sequential execution:** 521 → 522 → 523 (each depends on previous)
- **Fail-fast:** If manual testing fails, stop pipeline and report
- **Skip detection:** Check for existing comments before invoking workers
- **Single responsibility:** Each worker does one thing well

## Definition of Done

- [ ] Story ID validated
- [ ] Research phase: ln-521 invoked OR existing comment found
- [ ] Manual testing phase: ln-522 invoked OR existing results found
- [ ] Auto test planning phase: ln-523 invoked
- [ ] Test task created/updated in Linear
- [ ] Summary returned to ln-500-story-quality-gate

**Output:** Summary with phase results + test task URL

## Phase 6: Meta-Analysis

**MANDATORY READ:** Load `shared/references/meta_analysis_protocol.md`

Skill type: `planning-coordinator`. Run after all phases complete. Output to chat using the `planning-coordinator` format.

## Reference Files

- Workers: `../ln-521-test-researcher/SKILL.md`, `../ln-522-manual-tester/SKILL.md`, `../ln-523-auto-test-planner/SKILL.md`
- Caller: `../ln-500-story-quality-gate/SKILL.md`
- Risk-based testing: `shared/references/risk_based_testing_guide.md`

---

**Version:** 4.0.0
**Last Updated:** 2026-01-15
