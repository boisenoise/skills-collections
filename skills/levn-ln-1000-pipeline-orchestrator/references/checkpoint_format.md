# Checkpoint Format & Resume Protocol

Checkpoint files enable crash recovery without restarting stages from scratch.

## File Location

```
{project_root}/.pipeline/
  state.json              # Global pipeline state (lead writes)
  checkpoint-{storyId}.json  # Per-story checkpoint (worker writes)
```

## Checkpoint Schema

| Field | Type | Stage | Description |
|-------|------|-------|-------------|
| `storyId` | string | All | Story identifier (e.g., "PROJ-42") |
| `stage` | number | All | Current stage (0-3) |
| `agentId` | string | All | Worker's agent ID for Task resume |
| `tasksCompleted` | string[] | All | Task IDs already finished |
| `tasksRemaining` | string[] | All | Task IDs still pending |
| `lastAction` | string | All | Description of last completed action |
| `timestamp` | string | All | ISO 8601 timestamp |
| `planScore` | number | 0 | Task plan quality score from ln-300 (0-4) |
| `readiness` | number | 1 | Story readiness score from ln-310 (1-10) |
| `verdict` | string | 1, 3 | GO/NO-GO (Stage 1) or PASS/CONCERNS/WAIVED/FAIL (Stage 3) |
| `reason` | string | 1 | NO-GO reason from ln-310 (optional, only if verdict=NO-GO) |
| `qualityScore` | number | 3 | Quality gate score from ln-500 (0-100) |
| `issues` | string | 3 | Quality issues if FAIL (optional, only if verdict=FAIL) |

**Example (Stage 3 checkpoint with all relevant fields):**
```json
{
  "storyId": "PROJ-42",
  "stage": 3,
  "agentId": "abc-123-def",
  "tasksCompleted": ["PROJ-101", "PROJ-102", "PROJ-103", "PROJ-104", "PROJ-105"],
  "tasksRemaining": [],
  "lastAction": "Quality gate completed, verdict: PASS",
  "timestamp": "2026-02-14T14:30:00Z",
  "verdict": "PASS",
  "qualityScore": 92
}
```

## Pipeline State Schema

Lead writes ALL state variables to `.pipeline/state.json` on every heartbeat cycle. This enables full recovery on restart.

| Field | Type | Description |
|-------|------|-------------|
| `complete` | boolean | `false` while pipeline running, `true` before cleanup |
| `active_workers` | number | Current worker count |
| `stories_remaining` | number | Stories not yet DONE/PAUSED |
| `last_check` | string | ISO 8601 timestamp of last state update |
| `story_state` | object | `{storyId: "STAGE_0"\|"STAGE_1"\|...\|"DONE"\|"PAUSED"}` |
| `worker_map` | object | `{storyId: worker_name}` — assigned worker per story |
| `quality_cycles` | object | `{storyId: count}` — FAIL→retry counter (limit 2) |
| `validation_retries` | object | `{storyId: count}` — NO-GO retry counter (limit 1) |
| `crash_count` | object | `{storyId: count}` — crash respawn counter (limit 1) |
| `priority_queue_ids` | string[] | Remaining story IDs in priority order |
| `story_results` | object | `{storyId: {stage0: "...", stage1: "...", ...}}` — per-stage results for report |
| `infra_issues` | array | `[{phase, type, message}]` — infrastructure issues for report |
| `worktree_map` | object | `{storyId: worktree_dir \| null}` — story → worktree mapping |
| `depends_on` | object | `{storyId: [prerequisite IDs]}` — dependency graph |

**Example:**
```json
{
  "complete": false,
  "active_workers": 2,
  "stories_remaining": 3,
  "last_check": "2026-02-13T14:30:00Z",
  "story_state": { "API-427": "STAGE_2", "API-428": "STAGE_1" },
  "worker_map": { "API-427": "story-API-427-s2", "API-428": "story-API-428-s1" },
  "quality_cycles": { "API-427": 0, "API-428": 0 },
  "validation_retries": { "API-427": 0, "API-428": 0 },
  "crash_count": { "API-427": 0, "API-428": 0 },
  "priority_queue_ids": ["API-429", "API-430", "API-431"],
  "story_results": { "API-427": { "stage0": "skip", "stage1": "skip", "stage2": "Done" } },
  "infra_issues": [],
  "worktree_map": { "API-427": ".worktrees/story-API-427", "API-428": null },
  "depends_on": { "API-429": ["API-427"], "API-430": [] }
}
```

## Resume Protocol

Lead executes on confirmed crash (3-step protocol passed):

```
1. Read checkpoint: .pipeline/checkpoint-{id}.json

2. Try resume (preserves full agent context):
   Task(resume: checkpoint.agentId)
   IF resume succeeds → worker continues where it left off → DONE

3. Fallback — new worker with checkpoint context:
   prompt = worker_prompt(story, checkpoint.stage, business_answers, worktree_map[id]) + CHECKPOINT_RESUME block
   Task(name: "story-{id}-s{N}-retry", model: "opus", prompt: prompt, mode: "bypassPermissions", ...)
```

**CHECKPOINT_RESUME block** (appended to worker prompt):
```
CHECKPOINT RESUME — DO NOT re-execute completed work.
Tasks already completed: {tasksCompleted joined by ", "}
Tasks remaining: {tasksRemaining joined by ", "}
Last action: {lastAction}
Continue from remaining tasks only.
```

## Worker Write Protocol

Workers write checkpoints at these points:

| Stage | When to Write | Required Fields | Stage-Specific Fields |
|-------|--------------|----------------|----------------------|
| 0 (ln-300) | After tasks created | storyId, stage, agentId, timestamp, lastAction | **planScore** (0-4), tasksCompleted=[], tasksRemaining=[created task IDs] |
| 1 (ln-310) | After validation | storyId, stage, agentId, timestamp, lastAction | **readiness** (1-10), **verdict** (GO/NO-GO), **reason** (if NO-GO), tasksCompleted=[], tasksRemaining=[] |
| 2 (ln-400) | After EACH task completes | storyId, stage, agentId, timestamp, lastAction | Move task ID from remaining to completed |
| 3 (ln-500) | After quality gate | storyId, stage, agentId, timestamp, lastAction | **verdict** (PASS/CONCERNS/WAIVED/FAIL), **qualityScore** (0-100), **issues** (if FAIL), tasksCompleted=[all], tasksRemaining=[] |

**Stage-Specific Field Requirements:**
- **Stage 0:** MUST write `planScore` (task plan quality from ln-300)
- **Stage 1:** MUST write `readiness`, `verdict`; MUST write `reason` if verdict=NO-GO
- **Stage 2:** No stage-specific fields (task progress only)
- **Stage 3:** MUST write `verdict`, `qualityScore`; MUST write `issues` if verdict=FAIL

**Stage 2 is critical** — most work happens here, checkpoints after each task prevent losing progress.

---
**Version:** 1.0.0
**Last Updated:** 2026-02-14
