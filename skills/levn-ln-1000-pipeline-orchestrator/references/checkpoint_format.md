# Checkpoint Format & Resume Protocol

Checkpoint files enable crash recovery without restarting stages from scratch.

## File Location

```
{project_root}/.hex-skills/pipeline/
  state.json                 # Global pipeline state (CLI-managed)
  checkpoint-{storyId}.json  # Per-story checkpoint (written by `node $PIPELINE checkpoint`)
```

## Checkpoint Schema

| Field | Type | Stage | Description |
|-------|------|-------|-------------|
| `stage` | number | All | Current stage (0-3) |
| `started_at` | string | All | Stage start timestamp (ISO 8601) |
| `completed_at` | string | All | Stage completion timestamp (ISO 8601) |
| `tasks_completed` | string[] | All | Task IDs already finished |
| `tasks_remaining` | string[] | All | Task IDs still pending |
| `last_action` | string | All | Description of last completed action |
| `plan_score` | number | 0 | Task plan quality score from ln-300 (0-4) |
| `readiness` | number | 1 | Story readiness score from ln-310 (1-10) |
| `verdict` | string | 1, 3 | GO/NO-GO (Stage 1) or PASS/CONCERNS/WAIVED/FAIL (Stage 3) |
| `reason` | string | 1 | NO-GO reason from ln-310 (optional, only if verdict=NO-GO) |
| `quality_score` | number | 3 | Quality gate score from ln-500 (0-100) |
| `issues` | string | 3 | Quality issues if FAIL (optional, only if verdict=FAIL) |
| `agents_info` | string | 1, 3 | Aggregated agent review summary |
| `git_stats` | object | 2 | Parsed `git diff --stat` summary |
| `architecture_delta` | object | 3 | Optional architecture comparison captured on STAGE_3 entry |

**Example (Stage 3 checkpoint with all relevant fields):**
```json
{
  "stage": 3,
  "started_at": "2026-02-14T14:10:00Z",
  "completed_at": "2026-02-14T14:30:00Z",
  "tasks_completed": ["PROJ-101", "PROJ-102", "PROJ-103", "PROJ-104", "PROJ-105"],
  "tasks_remaining": [],
  "last_action": "Quality gate completed, verdict: PASS",
  "verdict": "PASS",
  "quality_score": 92,
  "agents_info": "codex(2/3),gemini(1/2)"
}
```

## Pipeline State Schema

CLI commands own `state.json`. The lead advances, pauses, and checkpoints via `node $PIPELINE ...` instead of mutating state fields manually.

| Field | Type | Description |
|-------|------|-------------|
| `story_id` | string | Story ID selected for this pipeline run |
| `story_title` | string | Selected Story title |
| `stage` | string | `QUEUED`, `STAGE_0`, `STAGE_1`, `STAGE_2`, `STAGE_3`, `DONE`, or `PAUSED` |
| `complete` | boolean | `false` while pipeline running, `true` after DONE/cancel |
| `quality_cycles` | number | FAIL->retry counter (limit 2) |
| `validation_retries` | number | NO-GO retry counter (limit 1) |
| `crash_count` | number | Confirmed crash counter |
| `storage_mode` | string | `"file"` or `"linear"` |
| `pipeline_start_time` | string | ISO 8601 pipeline start timestamp |
| `updated_at` | string | ISO 8601 timestamp of latest write |
| `project_brief` | object | `{name, tech, type, key_rules}` from target project |
| `story_briefs` | object | Orchestrator brief payloads keyed by story ID |
| `business_answers` | object | Answers captured in Phase 2 |
| `status_cache` | object | Linear status name->UUID mapping |
| `skill_repo_path` | string | Skills repository absolute path |
| `worktree_dir` | string | Active worktree path for this run |
| `branch_name` | string | Active branch name |
| `stage_timestamps` | object | `{stage_N_start, stage_N_end}` timestamps |
| `git_stats` | object | Code output metrics captured from stage checkpoints |
| `readiness_scores` | object | Readiness scores kept for reporting/quality decisions |
| `infra_issues` | array | Infrastructure issues for report |
| `previous_quality_score` | object | Previous FAIL score for degradation comparison |
| `story_results` | object | Per-stage reporting payload |
| `paused_reason` | string/null | Reason when pipeline is paused |

**Example:**
```json
{
  "story_id": "API-427",
  "story_title": "Implement API retry policy",
  "stage": "STAGE_2",
  "complete": false,
  "quality_cycles": 0,
  "validation_retries": 0,
  "crash_count": 0,
  "storage_mode": "linear",
  "pipeline_start_time": "2026-02-13T12:55:00Z",
  "updated_at": "2026-02-13T14:30:00Z",
  "project_brief": { "name": "API", "tech": "Node.js", "type": "API", "key_rules": ["Keep story status authoritative"] },
  "story_briefs": { "API-427": { "tech": "Node.js", "keyFiles": ["src/api/retry.ts"] } },
  "business_answers": {},
  "status_cache": { "Todo": "uuid-todo" },
  "skill_repo_path": "D:/Development/LevNikolaevich/claude-code-skills/skills-catalog",
  "worktree_dir": "D:/project/.hex-skills/worktrees/story-API-427",
  "branch_name": "feature/API-427-implement-api-retry-policy",
  "stage_timestamps": { "stage_2_start": "2026-02-13T13:00:00Z" },
  "git_stats": {},
  "readiness_scores": {},
  "infra_issues": [],
  "previous_quality_score": {},
  "story_results": {},
  "paused_reason": null
}
```

## Resume Protocol

Lead executes on crash recovery:

```
1. Bash: node $PIPELINE status --story {id}
2. Extract resume_action from JSON response
3. Follow resume_action (e.g., "Invoke Skill(ln-400) for stage 2")
```

CLI status includes reconciliation: if state.json and checkpoint disagree, pipeline is auto-PAUSED with recovery reason.

## Checkpoint Write Protocol

CLI writes checkpoints via `node $PIPELINE checkpoint` after each Skill() call:

| Stage | CLI Command |
|-------|-------------|
| 0 | `node $PIPELINE checkpoint --story {id} --stage 0 --plan-score {N} --tasks-remaining '{[...]}' --last-action "..."` |
| 1 | `node $PIPELINE checkpoint --story {id} --stage 1 --verdict GO --readiness {N} --agents-info "..." --last-action "..."` |
| 2 | `node $PIPELINE checkpoint --story {id} --stage 2 --tasks-completed '{[...]}' --git-stats '{...}' --last-action "..."` |
| 3 | `node $PIPELINE checkpoint --story {id} --stage 3 --verdict PASS --quality-score {N} --agents-info "..." --last-action "..."` |

**Stage-Specific Field Requirements:**
- **Stage 0:** `--plan-score` (0-4), `--tasks-remaining`
- **Stage 1:** `--readiness` (1-10), `--verdict` (GO/NO-GO); `--reason` if NO-GO
- **Stage 2:** `--tasks-completed`, `--git-stats`
- **Stage 3:** `--verdict` (PASS/CONCERNS/WAIVED/FAIL), `--quality-score` (0-100); `--issues` if FAIL

---
**Version:** 5.0.0
**Last Updated:** 2026-03-24
