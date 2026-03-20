# Checkpoint Format & Resume Protocol

Checkpoint files enable crash recovery without restarting stages from scratch.

## File Location

```
{project_root}/.pipeline/
  state.json              # Global pipeline state (lead writes)
  checkpoint-{storyId}.json  # Per-story checkpoint (lead writes after each stage)
```

## Checkpoint Schema

| Field | Type | Stage | Description |
|-------|------|-------|-------------|
| `storyId` | string | All | Story identifier (e.g., "PROJ-42") |
| `stage` | number | All | Current stage (0-3) |
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
  "tasksCompleted": ["PROJ-101", "PROJ-102", "PROJ-103", "PROJ-104", "PROJ-105"],
  "tasksRemaining": [],
  "lastAction": "Quality gate completed, verdict: PASS",
  "timestamp": "2026-02-14T14:30:00Z",
  "verdict": "PASS",
  "qualityScore": 92
}
```

## Pipeline State Schema

Lead writes ALL state variables to `.pipeline/state.json` on every stage transition. This enables full recovery on restart.

| Field | Type | Description |
|-------|------|-------------|
| `complete` | boolean | `false` while pipeline running, `true` before cleanup |
| `selected_story_id` | string | Story ID selected by user for this pipeline run |
| `stories_remaining` | number | 1 if story not yet DONE/PAUSED, else 0 |
| `last_check` | string | ISO 8601 timestamp of last state update |
| `story_state` | object | `{storyId: "STAGE_0"\|"STAGE_1"\|"STAGE_2"\|"STAGE_3"\|"DONE"\|"PAUSED"}` |
| `quality_cycles` | object | `{storyId: count}` — FAIL->retry counter (limit 2) |
| `previous_quality_score` | object | `{storyId: score}` — quality score from first Stage 3 FAIL (for rework degradation comparison). Absent until first FAIL. |
| `validation_retries` | object | `{storyId: count}` — NO-GO retry counter (limit 1) |
| `story_results` | object | `{storyId: {stage0: "...", stage1: "...", ...}}` — per-stage results for report |
| `infra_issues` | array | `[{phase, type, message}]` — infrastructure issues for report |
| `status_cache` | object | `{statusName: statusUUID}` — Linear status name->UUID mapping (empty if file mode) |
| `stage_timestamps` | object | `{storyId: {stage_N_start: ISO, stage_N_end: ISO}}` — per-stage duration tracking |
| `git_stats` | object | `{storyId: {lines_added, lines_deleted, files_changed}}` — code output metrics |
| `pipeline_start_time` | string | ISO 8601 timestamp of pipeline start — for wall-clock duration |
| `readiness_scores` | object | `{storyId: readiness_score}` — from Stage 1 GO, for Stage 3 fast-track decision |
| `business_answers` | object | `{question: answer}` from Phase 2 — passed to Skill prompts |
| `storage_mode` | string | `"file"` or `"linear"` — task storage backend |
| `skill_repo_path` | string | Skills repository absolute path (for recovery) |
| `project_brief` | object | `{name, tech, type, key_rules}` — project context from CLAUDE.md |
| `story_briefs` | object | `{storyId: {tech, keyFiles, approach, complexity}}` — orchestrator brief from Linear |

**Example:**
```json
{
  "complete": false,
  "selected_story_id": "API-427",
  "stories_remaining": 1,
  "last_check": "2026-02-13T14:30:00Z",
  "story_state": { "API-427": "STAGE_2" },
  "quality_cycles": { "API-427": 0 },
  "previous_quality_score": {},
  "validation_retries": { "API-427": 0 },
  "story_results": { "API-427": { "stage0": "skip", "stage1": "skip" } },
  "infra_issues": [],
  "stage_timestamps": { "API-427": { "stage_2_start": "2026-02-13T13:00:00Z" } },
  "git_stats": {},
  "pipeline_start_time": "2026-02-13T12:55:00Z"
}
```

## Resume Protocol

Lead executes on crash recovery:

```
1. Read checkpoint: .pipeline/checkpoint-{id}.json
2. Read state.json -> restore pipeline state variables
3. Resume from last checkpoint stage + 1
   Re-invoke Skill() for the failed stage with CHECKPOINT_RESUME context
```

**CHECKPOINT_RESUME block** (passed to Skill context):
```
CHECKPOINT RESUME — DO NOT re-execute completed work.
Tasks already completed: {tasksCompleted joined by ", "}
Tasks remaining: {tasksRemaining joined by ", "}
Last action: {lastAction}
Continue from remaining tasks only.
```

## Checkpoint Write Protocol

Lead writes checkpoints after each Skill() call completes:

| Stage | When to Write | Required Fields | Stage-Specific Fields |
|-------|--------------|----------------|----------------------|
| 0 (ln-300) | After tasks created | storyId, stage, timestamp, lastAction | **planScore** (0-4), tasksCompleted=[], tasksRemaining=[created task IDs] |
| 1 (ln-310) | After validation | storyId, stage, timestamp, lastAction | **readiness** (1-10), **verdict** (GO/NO-GO), **reason** (if NO-GO), tasksCompleted=[], tasksRemaining=[] |
| 2 (ln-400) | After implementation | storyId, stage, timestamp, lastAction | tasksCompleted=[done task IDs], tasksRemaining=[pending task IDs] |
| 3 (ln-500) | After quality gate | storyId, stage, timestamp, lastAction | **verdict** (PASS/CONCERNS/WAIVED/FAIL), **qualityScore** (0-100), **issues** (if FAIL), tasksCompleted=[all], tasksRemaining=[] |

**Stage-Specific Field Requirements:**
- **Stage 0:** MUST write `planScore` (task plan quality from ln-300)
- **Stage 1:** MUST write `readiness`, `verdict`; MUST write `reason` if verdict=NO-GO
- **Stage 2:** No stage-specific fields (task progress only)
- **Stage 3:** MUST write `verdict`, `qualityScore`; MUST write `issues` if verdict=FAIL

---
**Version:** 4.0.0
**Last Updated:** 2026-03-19
