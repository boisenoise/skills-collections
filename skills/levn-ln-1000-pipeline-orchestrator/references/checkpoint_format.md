# Checkpoint Format & Resume Protocol

Checkpoint files enable crash recovery without restarting stages from scratch.

## File Location

```
{project_root}/.pipeline/
  state.json              # Global pipeline state (lead writes)
  checkpoint-{storyId}.json  # Per-story checkpoint (worker writes)
```

## Checkpoint Schema

| Field | Type | Description |
|-------|------|-------------|
| `storyId` | string | Story identifier (e.g., "PROJ-42") |
| `stage` | number | Current stage (0-3) |
| `agentId` | string | Worker's agent ID for Task resume |
| `tasksCompleted` | string[] | Task IDs already finished |
| `tasksRemaining` | string[] | Task IDs still pending |
| `lastAction` | string | Description of last completed action |
| `timestamp` | string | ISO 8601 timestamp |

**Example:**
```json
{
  "storyId": "PROJ-42",
  "stage": 2,
  "agentId": "abc-123-def",
  "tasksCompleted": ["PROJ-101", "PROJ-102", "PROJ-103"],
  "tasksRemaining": ["PROJ-104", "PROJ-105"],
  "lastAction": "PROJ-103 completed, moved to To Review",
  "timestamp": "2026-02-13T14:30:00Z"
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

| Stage | When to Write | Key Fields |
|-------|--------------|------------|
| 0 (ln-300) | After tasks created | tasksCompleted=[], tasksRemaining=[created task IDs] |
| 1 (ln-310) | After validation | tasksCompleted=[], tasksRemaining=[] (validation is atomic) |
| 2 (ln-400) | After EACH task completes | Move task ID from remaining to completed |
| 3 (ln-500) | After quality gate | tasksCompleted=[all], tasksRemaining=[] |

**Stage 2 is critical** — most work happens here, checkpoints after each task prevent losing progress.

---
**Version:** 1.0.0
**Last Updated:** 2026-02-13
