# Phase 4: Pipeline Flow

Sequential Skill-based pipeline execution with ASSERT guards, stage notes, and recovery protocol.

## 1. ASSERT Guards (per stage)

After each Skill() call, re-read kanban and verify expected state:

| Stage | ASSERT | On failure |
|-------|--------|-----------|
| 0 (ln-300) | Tasks exist under Story, count IN 1..8 | PAUSED, ESCALATE |
| 1 (ln-310) | Story status = Todo | Retry once (validation_retries < 1). 2nd failure: PAUSED, ESCALATE |
| 2 (ln-400) | Story status = To Review AND all tasks = Done | PAUSED, ESCALATE |
| 3 (ln-500) | Story status = Done OR To Rework | If Done: BREAK. If To Rework: rework cycle |

## 2. Context Recovery

When auto-compaction compresses conversation during long pipelines, lead loses SKILL.md instructions and state variables.

**Detection:** Lead cannot recall pipeline variables, stage flow, or ASSERT guards.

**Recovery steps:**
1. Read `.pipeline/state.json` -> restore ALL state variables
2. Read this SKILL.md (FULL) -> restore phases, rules, error handling
3. Read `references/phases/phase4_flow.md` -> restore ASSERT guards and flow
4. Resume from last checkpoint stage + 1

**Trigger:** `PostCompact` hook (Claude Code 2.1.76+) or manual detection.

## 3. Error Handling

| Error type | Detection | Recovery |
|-----------|-----------|---------|
| Skill() returns error | Exception in lead | Read checkpoint -> re-invoke same Skill(). Kanban handles task-level resume (Done tasks skipped by coordinator query) |
| ASSERT fails | Kanban re-read shows unexpected state | Log issue, PAUSED, ESCALATE to user |
| Lead crash (session dies) | Phase 0 on next session | Read state.json + checkpoint -> jump to correct stage |

## 4. Stage Notes Template

Lead writes `.pipeline/stage_N_notes_{id}.md` after each Skill() call:

```
## {Stage Name}
**Skill:** ln-{NNN}
**Agent Review:** {agents_info or "N/A"}
### Key Decisions
- {1-3 bullets: rationale for major decisions, challenges resolved}
### Artifacts
- {Created files, URLs, commit SHAs}
```

**Agents info extraction:** Read from `.agent-review/review_history.md` (last entry) or parse from Skill output (look for "Agent Review:" display line). Format: `codex(2/3),gemini(1/2)` or `SKIPPED({reason})` or `N/A`.

## 5. Agents Info Format

Pipeline Report uses this format for agent review results:

| Value | Meaning |
|-------|---------|
| `codex(2/3),gemini(1/2)` | Both agents used; accepted/total suggestions |
| `codex(1/2),gemini(FAILED)` | One agent failed |
| `SKIPPED(no agents available)` | Health check returned 0 agents |
| `SKIPPED(fast-track)` | Fast-track mode reduced agent review |
| `N/A` | No agent info found |

---
**Version:** 1.0.0
**Last Updated:** 2026-03-19
