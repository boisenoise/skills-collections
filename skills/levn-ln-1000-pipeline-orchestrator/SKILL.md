---
name: ln-1000-pipeline-orchestrator
description: "Meta-orchestrator: reads kanban board, lets user pick ONE Story, drives it through pipeline 300->310->400->500 via TeamCreate. Creates worktree isolation; coordinates workers + reports."
license: MIT
---

> **Paths:** File paths (`shared/`, `references/`, `../ln-*`) are relative to skills repo root. If not found at CWD, locate this SKILL.md directory and go up one level for repo root.

# Pipeline Orchestrator

Meta-orchestrator that reads the kanban board, shows available Stories, lets the user pick one to process, and drives it through the full pipeline (task planning -> validation -> execution -> quality gate) using Claude Code Agent Teams.

## Purpose & Scope
- Parse kanban board and show available Stories for user selection
- Ask business questions in ONE batch before execution; make technical decisions autonomously
- Spawn worker via TeamCreate for selected Story (single worker)
- Drive selected Story through 4 stages: ln-300 -> ln-310 -> ln-400 -> ln-500
- Collect branch name + stats from worker reports, generate pipeline report
- Handle failures, retries, and escalation to user

## Hierarchy

```
L0: ln-1000-pipeline-orchestrator (TeamCreate lead, delegate mode, single story)
  +-- Worker (fresh per stage, shutdown after completion, one at a time)
       |   All stages: Opus 4.6  |  Effort: Stage 0 = low | Stage 1,2 = medium | Stage 3 = medium
       +-- L1: ln-300 / ln-310 / ln-400 / ln-500 (invoked via Skill tool, as-is)
            +-- L2/L3: existing hierarchy unchanged
```

**Key principle:** ln-1000 does NOT modify existing skills. Workers invoke ln-300/ln-310/ln-400/ln-500 through Skill tool exactly as a human operator would.

## MCP Tool Preferences

When `mcp__hashline-edit__*` tools are available, workers MUST prefer them over standard file tools:

| Standard Tool | Hashline-Edit Replacement | Why |
|---------------|--------------------------|-----|
| `Read` | `mcp__hashline-edit__read_file` | Hash-prefixed lines enable precise edits |
| `Edit` | `mcp__hashline-edit__edit_file` | Atomic validation prevents corruption |
| `Write` | `mcp__hashline-edit__write_file` | Same behavior, consistent interface |
| `Grep` | `mcp__hashline-edit__grep` | Results include hashline refs for follow-up edits |

**Fallback:** If hashline-edit MCP unavailable (tools not in ToolSearch), use standard tools. No error.

## Task Storage Mode

**MANDATORY READ:** Load `shared/references/tools_config_guide.md` and `shared/references/storage_mode_detection.md`

Extract: `task_provider` = Task Management → Provider (`linear` | `file`).

## When to Use
- One Story ready for processing — user picks which one
- Need end-to-end automation: task planning -> validation -> execution -> quality gate
- Want controlled Story processing with pipeline report

## Pipeline: 4-Stage State Machine

**MANDATORY READ:** Load `references/pipeline_states.md` for transition rules and guards.

```
Backlog       --> Stage 0 (ln-300) --> Backlog      --> Stage 1 (ln-310) --> Todo
(no tasks)        create tasks         (tasks exist)      validate            |
                                                          | NO-GO             |
                                                          v                   v
                                                       [retry/ask]    Stage 2 (ln-400)
                                                                             |
                                                                             v
                                                                      To Review
                                                                             |
                                                                             v
                                                                      Stage 3 (ln-500)
                                                                       |          |
                                                                      PASS       FAIL
                                                                       |          v
                                                                      Done    To Rework -> Stage 2
                                                               (branch pushed)  (max 2 cycles)
```

| Stage | Skill | Input Status | Output Status |
|-------|-------|-------------|--------------|
| 0 | ln-300-task-coordinator | Backlog (no tasks) | Backlog (tasks created) |
| 1 | ln-310-multi-agent-validator | Backlog (tasks exist) | Todo |
| 2 | ln-400-story-executor | Todo / To Rework | To Review |
| 3 | ln-500-story-quality-gate | To Review | Done / To Rework |

## Team Lead Responsibilities

This skill runs as a **team lead** in delegate mode. The agent executing ln-1000 MUST NOT write code or invoke skills directly.

| Responsibility | Description |
|---------------|-------------|
| **Coordinate** | Assign stages to worker, process completion reports, advance pipeline |
| **Verify board** | Re-read kanban/Linear after each stage. Workers update via skills; lead ASSERTs expected state transitions |
| **Escalate** | Route failures to user when retry limits exceeded |
| **Report** | Collect branch name + stats from worker, generate pipeline report |
| **Shutdown** | Graceful worker shutdown, team cleanup |

**NEVER do as lead:** Invoke ln-300/ln-310/ln-400/ln-500 directly. Edit source code. Skip quality gate. Force-kill workers.

## Workflow

### Phase 0: Recovery Check

```
IF .pipeline/state.json exists AND complete == false:
  # Previous run interrupted — resume from saved state
  1. Read .pipeline/state.json → restore: selected_story_id, story_state, worker_map,
     quality_cycles, validation_retries, crash_count,
     story_results, infra_issues,
     stage_timestamps, git_stats, pipeline_start_time, readiness_scores
  2. Read .pipeline/checkpoint-{selected_story_id}.json → validate story_state consistency
     (checkpoint.stage should match story_state[id])
  3. Re-read kanban board → verify selected story still exists
  4. Read team config → verify worker_map members still exist
  5. Set suspicious_idle = false (ephemeral, reset on recovery)
  5a. IF worktree_dir exists (.worktrees/story-{selected_story_id}): cd {worktree_dir}
  6. IF story_state[id] IN ("STAGE_0".."STAGE_3"):
     IF checkpoint.agentId exists → Task(resume: checkpoint.agentId)
     ELSE → respawn worker with checkpoint context (see checkpoint_format.md)
  7. Jump to Phase 4 event loop

IF .pipeline/state.json NOT exists OR complete == true:
  # Fresh start — proceed to Phase 1
```

### Phase 1: Discovery, Kanban Parsing & Story Selection

**MANDATORY READ:** Load `references/kanban_parser.md` for parsing patterns.

1. Auto-discover `docs/tasks/kanban_board.md` (or Linear API via storage mode operations)
2. Extract project brief from target project's CLAUDE.md (NOT skills repo):
   ```
   project_brief = {
     name: <from H1 or first line>,
     tech: <from Development Commands / tech references>,
     type: <inferred: "CLI", "API", "web app", "library">,
     key_rules: <2-3 critical rules>
   }
   IF not found: project_brief = { name: basename(project_root), tech: "unknown" }
   ```
3. Parse all status sections: Backlog, Todo, In Progress, To Review, To Rework
4. Extract Story list with: ID, title, status, Epic name, task presence
5. Filter: skip Stories in Done, Postponed, Canceled
6. Detect task presence per Story:
   - Has `_(tasks not created yet)_` → **no tasks** → Stage 0
   - Has task lines (4-space indent) → **tasks exist** → Stage 1+
7. Determine target stage per Story (see `references/pipeline_states.md` Stage-to-Status Mapping)
8. Show available Stories and ask user to pick ONE:
   ```
   Project: {project_brief.name} ({project_brief.tech})

   Available Stories:
   | # | Story | Status | Stage | Skill | Epic |
   |---|-------|--------|-------|-------|------|
   | 1 | PROJ-42: Auth endpoint | To Review | 3 | ln-500 | Epic: Auth |
   | 2 | PROJ-55: CRUD users | Backlog (no tasks) | 0 | ln-300 | Epic: Users |
   | 3 | PROJ-60: Dashboard | Todo | 2 | ln-400 | Epic: UI |

   AskUserQuestion: "Which story to process? Enter # or Story ID."
   ```
9. Store selected story. Extract story brief for selected story only:
   ```
   description = get_issue(selected_story.id).description
   story_briefs[id] = parse <!-- ORCHESTRATOR_BRIEF_START/END --> markers
   IF no markers: story_briefs[id] = { tech: project_brief.tech, keyFiles: "unknown" }
   ```

### Phase 2: Pre-flight Questions (ONE batch)

1. Load selected Story description (metadata only)
2. Scan for business ambiguities — questions where:
   - Answer cannot be found in codebase, docs, or standards
   - Answer requires business/product decision (payment provider, auth flow, UI preference)
3. Collect ALL business questions into single AskUserQuestion:
   ```
   "Before starting Story {selected_story.id}:
    Which payment provider? (Stripe/PayPal/both)
    Auth flow — JWT or session-based?"
   ```
4. Technical questions — resolve using project_brief:
   - Library versions: MCP Ref / Context7 (for `project_brief.tech` ecosystem)
   - Architecture patterns: `project_brief.key_rules`
   - Standards compliance: ln-310 Phase 2 handles this
5. Store answers in shared context (pass to worker via spawn prompt)

**Skip Phase 2** if no business questions found. Proceed directly to Phase 3.

### Phase 3: Team Setup

**MANDATORY READ:** Load `references/settings_template.json` for required permissions and hooks.

#### 3.0 Linear Status Cache (Linear mode only)

```
IF storage_mode == "linear":
  statuses = list_issue_statuses(teamId=team_id)
  status_cache = {status.name: status.id FOR status IN statuses}

  REQUIRED = ["Backlog", "Todo", "In Progress", "To Review", "To Rework", "Done"]
  missing = [s for s in REQUIRED if s not in status_cache]
  IF missing: ABORT "Missing Linear statuses: {missing}. Configure workflow."

  # Persist in state.json (added in 3.2) and pass to workers via prompt CONTEXT
```

#### 3.1 Pre-flight: Settings Verification

Verify `.claude/settings.local.json` in target project:
- `defaultMode` = `"bypassPermissions"` (required for workers)
- `hooks.Stop` registered → `pipeline-keepalive.sh`
- `hooks.TeammateIdle` registered → `worker-keepalive.sh`

If missing or incomplete → copy from `references/settings_template.json` and install hook scripts via Bash `cp` (NOT Write tool — Write produces CRLF on Windows, breaking `#!/bin/bash` shebang):
```
# Preflight: verify dependencies
which jq || ABORT "jq is required for pipeline hooks. Install: https://jqlang.github.io/jq/download/"

mkdir -p .claude/hooks
Bash: cp {skill_repo}/ln-1000-pipeline-orchestrator/references/hooks/pipeline-keepalive.sh .claude/hooks/pipeline-keepalive.sh
Bash: cp {skill_repo}/ln-1000-pipeline-orchestrator/references/hooks/worker-keepalive.sh  .claude/hooks/worker-keepalive.sh
```

**Hook troubleshooting:** If hooks fail with "No such file or directory":
1. Verify hook commands use `bash .claude/hooks/script.sh` (relative path, no env vars — `$CLAUDE_PROJECT_DIR` is NOT available in hook shell context)
2. Verify `.claude/hooks/*.sh` files exist and have `#!/bin/bash` shebang
3. On Windows: ensure LF line endings in .sh files (see hook installation above — use Bash `cp`, not Write tool)

#### 3.2 Initialize Pipeline State

```
Write .pipeline/state.json (full schema — see checkpoint_format.md):
  { "complete": false, "selected_story_id": "<selected story ID>",
    "stories_remaining": 1, "last_check": <now>,
    "story_state": {}, "worker_map": {}, "quality_cycles": {}, "validation_retries": {},
    "crash_count": {},
    "story_results": {}, "infra_issues": [],    # story_results includes stage{N}_agents for Stage 1/3
    "status_cache": {<status_name: status_uuid>},    # Empty object if file mode
    "stage_timestamps": {}, "git_stats": {}, "pipeline_start_time": <now>, "readiness_scores": {},
    "skill_repo_path": <absolute path to skills repository root>,
    "team_name": "pipeline-{YYYY-MM-DD}",
    "business_answers": {<question: answer pairs from Phase 2, or {} if skipped>},
    "storage_mode": "file"|"linear",
    "project_brief": {<name, tech, type, key_rules from Phase 1 step 2>},
    "story_briefs": {<storyId: {tech, keyFiles, approach, complexity} from Phase 1 step 9>} }   # Recovery-critical
Write .pipeline/lead-session.id with current session_id   # Stop hook uses this to only keep lead alive
```

#### 3.2a Sleep Prevention (Windows only)

```
IF platform == "win32":
  Bash: cp {skill_repo}/ln-1000-pipeline-orchestrator/references/hooks/prevent-sleep.ps1 .claude/hooks/prevent-sleep.ps1
  Bash: powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File .claude/hooks/prevent-sleep.ps1 &
  sleep_prevention_pid = $!
  # Script polls .pipeline/state.json — self-terminates when complete=true
  # Fallback: Windows auto-releases execution state on process exit
```

#### 3.3 Create Team

**Model routing:** All stages use `model: "opus"`. Effort routing via prompt: `effort_for_stage(0) = "low"`, `effort_for_stage(1) = "medium"`, `effort_for_stage(2) = "medium"`, `effort_for_stage(3) = "medium"`. Crash recovery = same as target stage. Thinking mode: always enabled (adaptive).

1. Create team:
   ```
   TeamCreate(team_name: "pipeline-{YYYY-MM-DD}-{HHmm}")
   ```

#### 3.4 Worktree Isolation

**MANDATORY READ:** Load `shared/references/git_worktree_fallback.md`

```
branch_check = git branch --show-current
IF branch_check matches feature/* / optimize/* / upgrade/* / modernize/*:
  # Already isolated — skip (standalone ln-400 created it earlier)
  worktree_dir = CWD
ELSE:
  # Create worktree so ALL workers (Stage 0-3) operate in feature branch
  story_slug = slugify(selected_story.title)    # lowercase, spaces→dashes
  branch = "feature/{selected_story_id}-{story_slug}"
  worktree_dir = ".worktrees/story-{selected_story_id}"

  # Carry uncommitted changes (per git_worktree_fallback.md steps 2-3a)
  changes = git diff HEAD
  IF changes not empty:
    git diff HEAD > .pipeline/carry-changes.patch

  git fetch origin && git merge origin/master
  git worktree add {worktree_dir} -b {branch}

  IF .pipeline/carry-changes.patch exists:
    git -C {worktree_dir} apply .pipeline/carry-changes.patch && rm .pipeline/carry-changes.patch
    IF apply fails: WARN user "Patch conflicts — continuing without uncommitted changes"

  cd {worktree_dir}    # All subsequent workers inherit this CWD
```

Workers self-detect `feature/*` on startup → skip their own worktree creation (ln-400 Phase 1 step 5).

### Phase 4: Execution Loop

**MANDATORY READ:** Load `references/message_protocol.md` for exact message formats and parsing regex.
**MANDATORY READ:** Load `references/worker_health_contract.md` for crash detection and respawn rules.

**Lead operates in delegate mode — coordination only, no code writing.**

**MANDATORY READ:** Load `references/checkpoint_format.md` for checkpoint schema and resume protocol.

```
# --- INITIALIZATION (single story) ---
selected_story = <from Phase 1 selection>
quality_cycles[selected_story.id] = 0       # FAIL→retry counter, limit 2
validation_retries[selected_story.id] = 0   # NO-GO retry counter, limit 1
crash_count[selected_story.id] = 0          # crash respawn counter, limit 1
suspicious_idle = false                      # crash detection flag
story_state[selected_story.id] = "QUEUED"
worker_map = {}                              # {storyId: worker_name}
story_results = {}                           # {storyId: {stage0: "...", stage1_agents: "...", stage3_agents: "...", ...}} — for pipeline report
infra_issues = []                            # [{phase, type, message}] — infrastructure problems
heartbeat_count = 0                          # Heartbeat cycle counter (ephemeral, resets on recovery)
stage_timestamps = {}                        # {storyId: {stage_N_start: ISO, stage_N_end: ISO}}
git_stats = {}                               # {storyId: {lines_added, lines_deleted, files_changed}}
pipeline_start_time = now()                  # ISO 8601 — wall-clock start for duration metrics
readiness_scores = {}                        # {storyId: readiness_score} — from Stage 1 GO

# Helper functions — defined in phase4_heartbeat.md (loaded above)
# skill_name_from_stage(stage), predict_next_step(stage), stage_duration(id, N)

# --- SPAWN SINGLE WORKER ---
id = selected_story.id
target_stage = determine_stage(selected_story)    # pipeline_states.md guards
worker_name = "story-{id}-s{target_stage}"

Task(name: worker_name, team_name: "pipeline-{date}",
     model: "opus", mode: "bypassPermissions",
     subagent_type: "general-purpose",
     prompt: worker_prompt(selected_story, target_stage, business_answers))
worker_map[id] = worker_name
story_state[id] = "STAGE_{target_stage}"
stage_timestamps[id] = {}
stage_timestamps[id]["stage_{target_stage}_start"] = now()
Write .pipeline/worker-{worker_name}-active.flag     # For TeammateIdle hook
Update .pipeline/state.json
SendMessage(recipient: worker_name,
            content: "Execute Stage {target_stage} for {id}",
            summary: "Stage {target_stage} assignment")

# --- EVENT LOOP (driven by Stop hook heartbeat, single story) ---
# HOW THIS WORKS:
# 1. Lead's turn ends → Stop event fires
# 2. pipeline-keepalive.sh reads .pipeline/state.json → complete=false → exit 2
# 3. stderr "HEARTBEAT: ..." → new agentic loop iteration
# 4. Any queued worker messages (SendMessage) delivered in this cycle
# 5. Lead processes messages via ON handlers (reactive) + verifies done-flags (proactive)
# 6. Lead's turn ends → Go to step 1
#
# The Stop hook IS the event loop driver. Each heartbeat = one iteration.
# Lead MUST NOT say "waiting for messages" and stop — the heartbeat keeps it alive.
# If no worker messages arrived: output brief status, let turn end → next heartbeat.
#
# --- CONTEXT RECOVERY PROTOCOL ---
# Claude Code may compress conversation history during long pipelines.
# When this happens, you lose SKILL.md instructions and state variables.
# The Stop hook includes "---PIPELINE RECOVERY CONTEXT---" in EVERY heartbeat stderr.
#
# IF you see this block and don't recall the pipeline protocol:
#   Follow CONTEXT RECOVERY PROTOCOL in references/phases/phase4_heartbeat.md (7 steps).
#   Quick summary: state.json → SKILL.md(FULL) → handlers → heartbeat → known_issues → ToolSearch → resume
#
# FRESH WORKER PER STAGE: Each stage transition = shutdown old worker + spawn new one.
#
# BIDIRECTIONAL HEALTH MONITORING:
# - Reactive: ON handlers process worker completion messages
# - Proactive: Verify done-flags without messages (lost message recovery)
# - Defense-in-depth: Handles network issues, context overflow, worker crashes

WHILE story_state[id] NOT IN ("DONE", "PAUSED"):

  # 1. Process worker messages (reactive message handling)
  #
  **MANDATORY READ:** Load `references/phases/phase4_handlers.md` for all ON message handlers:
  - Stage 0 COMPLETE / ERROR (task planning outcomes)
  - Stage 1 COMPLETE (GO / NO-GO validation outcomes with retry logic)
  - Stage 2 COMPLETE / ERROR (execution outcomes)
  - Stage 3 COMPLETE (PASS/CONCERNS/WAIVED/FAIL quality gate outcomes with rework cycles)
  - Worker crash detection (3-step protocol: flag → probe → respawn)

  Handlers include sender validation and state guards to prevent duplicate processing.

  # 2. Active done-flag verification (proactive health monitoring)
  #
  **MANDATORY READ:** Load `references/phases/phase4_heartbeat.md` for bidirectional health monitoring:
  - Lost message detection (done-flag exists but state not advanced)
  - Synthetic recovery from checkpoint + kanban verification (all 4 stages)
  - Fallback to probe protocol when checkpoint missing
  - Structured heartbeat output (single story status line)
  - Helper functions (skill_name_from_stage, predict_next_step)

  # 3. Heartbeat state persistence
  #
  ON HEARTBEAT (Stop hook stderr: "HEARTBEAT: ..."):
    Write .pipeline/state.json with ALL state variables.
    # phase4_heartbeat.md persistence details (loaded above)

```

**`determine_stage(story)` routing:** Stage-to-Status Mapping table in `references/pipeline_states.md` (loaded above).

> **Worktree** created by ln-1000 in Phase 3.4 — all workers operate in `feature/*`. **Branch finalization** (commit, push, worktree cleanup) is handled by ln-500 after quality gate verdict. ln-1000 collects the branch name + stats from the worker's completion report.

### Phase 5: Cleanup & Report

```
# 0. Signal pipeline complete (allows Stop hook to pass)
Write .pipeline/state.json: { "complete": true, ... }

# 1. Self-verify against Definition of Done
verification = {
  story_selected:   selected_story_id is set              # Phase 1 ✓
  questions_asked:  business_answers stored OR none        # Phase 2 ✓
  team_created:     team exists                            # Phase 3 ✓
  story_processed:  story_state[id] IN ("DONE", "PAUSED") # Phase 4 ✓
}
IF ANY verification == false: WARN user with details

# 2. Read stage notes (written by workers in .pipeline/)
stage_notes = {}
FOR N IN 0..3:
  IF .pipeline/stage_{N}_notes_{id}.md exists:
    stage_notes[N] = read file content
  ELSE:
    stage_notes[N] = "(no notes captured)"

# 3. Finalize pipeline report
durations = {N: stage_timestamps[id]["stage_{N}_end"] - stage_timestamps[id]["stage_{N}_start"]
             FOR N IN 0..3 IF both timestamps exist}

Write docs/tasks/reports/pipeline-{date}.md:

  # Pipeline Report — {date}

  **Story:** {selected_story_id} — {title}
  **Branch:** {branch_name from worker report}
  **Final State:** {story_state[id]}
  **Duration:** {now() - pipeline_start_time}

  ## Task Planning (ln-300)
  | Tasks | Plan Score | Duration |
  |-------|-----------|----------|
  | {N} created | {score}/4 | {durations[0]} |

  {stage_notes[0] — Key Decisions + Artifacts sections}

  ## Validation (ln-310)
  | Verdict | Readiness | Agent Review | Duration |
  |---------|-----------|-------------|----------|
  | {verdict} | {score}/10 | {story_results[id].stage1_agents} | {durations[1]} |

  {stage_notes[1] — Key Decisions + Artifacts sections}

  ## Implementation (ln-400)
  | Status | Files | Lines | Duration |
  |--------|-------|-------|----------|
  | {result} | {git_stats[id].files_changed} | +{git_stats[id].lines_added}/-{git_stats[id].lines_deleted} | {durations[2]} |

  {stage_notes[2] — Key Decisions + Artifacts sections}

  ## Quality Gate (ln-500)
  | Verdict | Score | Agent Review | Rework | Duration |
  |---------|-------|-------------|--------|----------|
  | {verdict} | {score}/100 | {story_results[id].stage3_agents} | {quality_cycles[id]} | {durations[3]} |

  {stage_notes[3] — Key Decisions + Artifacts sections}

  ## Pipeline Metrics
  | Wall-clock | Workers | Crashes | Validation retries | Infra issues |
  |------------|---------|---------|-------------------|--------------|
  | {total_duration} | {worker_spawn_count} | {crash_count[id]} | {validation_retries[id]} | {len(infra_issues)} |

  {IF infra_issues: list each issue with phase, type, message}

# 4. Show pipeline summary to user
```
Pipeline Complete:
| Story | Branch | Planning | Validation | Implementation | Quality Gate | State |
|-------|--------|----------|------------|----------------|-------------|-------|
| {id} | {branch} | {stage0} | {stage1} | {stage2} | {stage3} | {story_state[id]} |

Report saved: docs/tasks/reports/pipeline-{date}.md
```

# 5. Shutdown worker (if still active)
IF worker_map[id]:
  SendMessage(type: "shutdown_request", recipient: worker_map[id])

# 6. Cleanup team
TeamDelete

# 7. Stop sleep prevention (Windows safety net)
IF sleep_prevention_pid:
  kill $sleep_prevention_pid 2>/dev/null || true

# 8. Remove pipeline state files
Delete .pipeline/ directory

# 9. Report results and report location to user
```

## Kanban as Single Source of Truth

- **Lead = single writer** to kanban_board.md. Workers report results via SendMessage; lead updates the board
- **Re-read board** after each stage completion for fresh state
- **Update algorithm:** Follow `shared/references/kanban_update_algorithm.md` for Epic grouping and indentation

## Error Handling

| Situation | Detection | Action |
|-----------|----------|--------|
| ln-300 task creation fails | Worker reports error | Escalate to user: "Cannot create tasks for Story {id}" |
| ln-310 NO-GO (Score <5) | Worker reports NO-GO | Retry once (ln-310 auto-fixes). If still NO-GO -> ask user |
| Task in To Rework 3+ times | Worker reports rework loop | Escalate: "Task X reworked 3 times, need input" |
| ln-500 FAIL | Worker reports FAIL verdict | Fix tasks auto-created by ln-500. Stage 2 re-entry. Max 2 quality cycles |
| Worker crash | TeammateIdle without completion msg | Re-spawn worker, resume from last stage |
| Business question mid-execution | Worker encounters ambiguity | Worker -> lead -> user -> lead -> worker (message chain) |

## Critical Rules

1. **Single Story processing.** One worker at a time. User selects which Story to process
2. **Delegate mode.** Lead coordinates only — never invoke ln-300/ln-310/ln-400/ln-500 directly. Workers do all execution
3. **Skills as-is.** Never modify or bypass existing skill logic. Workers call `Skill("ln-310-multi-agent-validator", args)` exactly as documented
4. **Kanban verification.** Workers update Linear/kanban via skills. Lead re-reads and ASSERTs expected state after each stage. In file mode, lead resolves merge conflicts
5. **Quality cycle limit.** Max 2 quality FAILs per Story (original + 1 rework cycle). After 2nd FAIL, escalate to user
6. **Worktree creation only.** ln-1000 creates worktree in Phase 3.4 so all workers start in feature branch. Branch finalization (commit, push, cleanup) owned by ln-500. ln-1000 does NOT merge or cleanup worktrees
7. **Re-read kanban.** After every stage completion, re-read board for fresh state. Never cache
8. **Graceful shutdown.** Always shutdown workers via shutdown_request. Never force-kill

## Known Issues

**MANDATORY READ:** Load `references/known_issues.md` for production-discovered problems and self-recovery patterns.

## Anti-Patterns
- Running ln-300/ln-310/ln-400/ln-500 directly from lead instead of delegating to workers
- Processing multiple stories without user selection
- Creating worktrees outside Phase 3.4 or managing branches post-creation (finalization owned by ln-500)
- Lead skipping kanban verification after worker updates (workers write via skills, lead MUST re-read + ASSERT)
- Skipping quality gate after execution
- Caching kanban state instead of re-reading
- Reading `~/.claude/teams/*/inboxes/*.json` directly (messages arrive automatically)
- Using `sleep` + filesystem polling for message checking
- Parsing internal Claude Code JSON formats (permission_request, idle_notification)
- Reusing same worker across stages (context exhaustion — spawn fresh worker per stage)
- Processing messages without verifying sender matches worker_map (stale message confusion from old/dead workers)

## Plan Mode Support

When invoked in Plan Mode, show available Stories and ask user which one to plan for:

1. Parse kanban board (Phase 1 steps 1-7)
2. Show available Stories table
3. AskUserQuestion: "Which story to plan for? Enter # or Story ID."
4. Execute Phase 2 (pre-flight questions) if business ambiguities found
5. Resolve `skill_repo_path` — absolute path to skills repo root (locate this SKILL.md, go up one level)
6. Show execution plan for selected Story
7. Write plan to plan file (using format below), call ExitPlanMode

**Plan Output Format:**
```
## Pipeline Plan for {date}

> **BEFORE EXECUTING — MANDATORY READ:** Load `{skill_repo_path}/ln-1000-pipeline-orchestrator/SKILL.md` (full file).
> This plan requires Agent Teams (TeamCreate), worktree isolation, delegate mode, and heartbeat event loop.
> The executing agent MUST NOT write code or invoke skills directly — only coordinate workers.
> After reading SKILL.md, start from Phase 3 (Team Setup) using the context below.

**Story:** {ID}: {Title}
**Current Status:** {status}
**Target Stage:** {N} ({skill_name})
**Storage Mode:** {file|linear}
**Project Brief:** {name} ({tech})
**Business Answers:** {answers from Phase 2, or "none"}
**Skill Repo Path:** {skill_repo_path}

### Execution Sequence
1. Read full SKILL.md + references (Phase 3 prerequisites)
2. TeamCreate("pipeline-{date}")
3. Spawn worker -> Stage {N} ({skill_name})
4. Drive through remaining stages via heartbeat event loop
5. Collect branch name + stats from worker reports
6. Generate pipeline report
7. Cleanup (Phase 5)

### Task Decomposition (from planning phase)
{task breakdown if available from Plan agent research}
```

## Definition of Done (self-verified in Phase 5)

| # | Criterion | Verified By |
|---|-----------|-------------|
| 1 | User selected Story from kanban board | `selected_story_id` is set |
| 2 | Business questions asked in single batch (or none found) | `business_answers` stored OR skip |
| 3 | Team created, single worker spawned | Worker spawned for selected Story |
| 4 | Selected Story processed: state = DONE or PAUSED | `story_state[id] IN ("DONE", "PAUSED")` |
| 5 | Pipeline report generated with branch name, stats, verdict | Report file exists |
| 6 | Pipeline summary shown to user | Phase 5 table output |
| 7 | Team cleaned up (worker shutdown, TeamDelete) | TeamDelete called |

## Reference Files

### Phase 4 Procedures (Progressive Disclosure)
- **Message handlers:** `references/phases/phase4_handlers.md` (Stage 0-3 ON handlers, crash detection)
- **Heartbeat & verification:** `references/phases/phase4_heartbeat.md` (Active done-flag checking, structured heartbeat output)

### Core Infrastructure
- **MANDATORY READ:** `shared/references/git_worktree_fallback.md`
- **MANDATORY READ:** `shared/references/research_tool_fallback.md`
- **Pipeline states:** `references/pipeline_states.md`
- **Worker prompts:** `references/worker_prompts.md`
- **Worker health:** `references/worker_health_contract.md`
- **Checkpoint format:** `references/checkpoint_format.md`
- **Message protocol:** `references/message_protocol.md`
- **Known issues:** `references/known_issues.md` (production-discovered problems and self-recovery)
- **Kanban parsing:** `references/kanban_parser.md`
- **Kanban update algorithm:** `shared/references/kanban_update_algorithm.md`
- **Settings template:** `references/settings_template.json`
- **Hooks:** `references/hooks/pipeline-keepalive.sh`, `references/hooks/worker-keepalive.sh`
- **Tools config:** `shared/references/tools_config_guide.md`
- **Storage mode operations:** `shared/references/storage_mode_detection.md`
- **Auto-discovery patterns:** `shared/references/auto_discovery_pattern.md`

### Delegated Skills
- `../ln-300-task-coordinator/SKILL.md`
- `../ln-310-multi-agent-validator/SKILL.md`
- `../ln-400-story-executor/SKILL.md`
- `../ln-500-story-quality-gate/SKILL.md`

---
**Version:** 2.0.0
**Last Updated:** 2026-02-25
