# Worker Prompt Templates

Templates for spawning story-workers via Task tool with team_name.

## Message Format Contract

**CRITICAL:** All worker reports MUST use exact message formats defined in `references/message_protocol.md`. Lead parses messages by regex — deviations trigger escalation.

**Key rules:**
- Use `SendMessage(type: "message", recipient: "pipeline-lead")` for all reports
- `content` must match exact format from protocol (Stage N COMPLETE/ERROR for {id}...)
- `summary` must be `"{id} Stage {N} {result}"` (max 10 words)
- After reporting, approve shutdown when lead requests it — never advance to next stage autonomously

**Diagnostic response:** When lead sends `"Status check"`, respond with:
```
Status for {id}: Stage {N} {EXECUTING|WAITING|ERROR}. Current step: {description}.
```

## Communication Rules

**All workers MUST follow these rules:**
- NEVER read `~/.claude/teams/*/inboxes/*.json` or any `~/.claude/` internal files
- NEVER use `sleep` loops or filesystem polling to check for messages
- Messages from lead arrive **automatically** as conversation turns
- Use **ONLY** `SendMessage` to communicate with lead
- After reporting, approve shutdown immediately — do not poll, do not sleep, do not read inbox files

## Checkpoint Protocol

Workers write checkpoint files after significant steps to enable crash recovery. See `references/checkpoint_format.md` for complete schema.

**Base fields (all stages):**
```json
{
  "storyId": "{storyId}",
  "stage": {N},
  "agentId": "<your agent ID from Task context>",
  "tasksCompleted": ["<completed task IDs>"],
  "tasksRemaining": ["<remaining task IDs>"],
  "lastAction": "<description of last completed action>",
  "timestamp": "<ISO 8601>"
}
```

**Stage-specific required fields:**
- **Stage 0:** Add `"planScore": <0-4>` (task plan quality from ln-300)
- **Stage 1:** Add `"readiness": <1-10>`, `"verdict": "GO|NO-GO"`, `"reason": "<reason>"` (reason only if NO-GO)
- **Stage 2:** No additional fields
- **Stage 3:** Add `"verdict": "PASS|CONCERNS|WAIVED|FAIL"`, `"qualityScore": <0-100>`, `"issues": "<issues>"` (issues only if FAIL)

| Stage | When to Write | Critical Fields |
|-------|--------------|----------------|
| 0 | After tasks created | planScore, tasksRemaining |
| 1 | After validation completes | readiness, verdict, reason (if NO-GO) |
| 2 | After EACH task completes (critical — most work happens here) | tasksCompleted/tasksRemaining tracking |
| 3 | After quality gate completes | verdict, qualityScore, issues (if FAIL) |

## Spawn Template

```
Task(
  name: "story-{storyId}-s{stage}",
  team_name: "pipeline-{date}",
  model: "opus",                     # All stages use Opus. Effort differentiated via prompt.
  mode: "bypassPermissions",
  subagent_type: "general-purpose",
  prompt: <use appropriate template below based on target stage>
)
```

**Note:** ln-1000 creates worktree in Phase 3.4 — all workers start in `feature/*` branch. Workers self-detect via `git branch --show-current` (per `shared/references/git_worktree_fallback.md`). ln-400 skips its own worktree creation when already on `feature/*`. `PIPELINE_DIR` = absolute path to `{project_root}/.pipeline` (set by lead in Phase 3.2).

**Worker name:** The `{workerName}` variable in templates = the `name` parameter from Task() spawn. Workers derive it from prompt context: `story-{storyId}-s{stage}` (or `-retry` suffix for retries).

## Stage 0: Task Planning (ln-300)

```
You are a pipeline worker in team "pipeline-{date}".
THINKING: Always enabled (adaptive). Reasoning effort: low.
- Think efficiently. Template-based task creation — apply Foundation-First pattern, fill template fields. Don't overanalyze.
Your assignment: Story {storyId} "{storyTitle}"

GIT CONTEXT: Worker self-detects branch via `git branch --show-current`.
If on feature/* branch — work here (ln-1000 creates worktree before spawning workers).
PIPELINE_DIR: {pipeline_dir}
ALL .pipeline/ file operations (checkpoint, done.flag) use PIPELINE_DIR (absolute path).

TASK: Execute Stage 0 — Task Planning (create implementation tasks).

Step 1: Invoke task coordinator:
  Skill(skill: "ln-300-task-coordinator", args: "{storyId}")

Step 2: After ln-300 completes, check result:
  - Tasks created successfully (1-8 tasks): Report success (Step 4a)
  - Error or plan score <2/4: Report failure (Step 4b)

Step 2b: Write stage notes to {PIPELINE_DIR}/stage_0_notes_{storyId}.md:
  ## Task Planning
  **Skill:** ln-300
  ### Key Decisions
  - {1-3 bullets: task decomposition rationale, Foundation-First pattern choices}
  ### Artifacts
  - {Task file paths or Linear task URLs created}

Step 3: Write checkpoint:
  Write {PIPELINE_DIR}/checkpoint-{storyId}.json with:
    stage=0, tasksCompleted=[], tasksRemaining=[created task IDs],
    planScore={score from ln-300 (0-4)}

Step 4a: Report SUCCESS to lead:
  SendMessage(type: "message", recipient: "pipeline-lead",
    content: "Stage 0 COMPLETE for {storyId}. {N} tasks created. Plan score: {score}/4.",
    summary: "{storyId} Stage 0 {N} tasks")
Step 4b: Report ERROR to lead (if Step 2 failed):
  SendMessage(type: "message", recipient: "pipeline-lead",
    content: "Stage 0 ERROR for {storyId}: {details}",
    summary: "{storyId} Stage 0 ERROR")
Step 5: Wait for ACK from lead:
  Lead will send "ACK Stage 0 for {storyId}" after processing your report.
  - ON ACK received: Write {PIPELINE_DIR}/worker-{workerName}-done.flag -> approve next shutdown_request
  - ON shutdown_request (no explicit ACK): Write done.flag -> approve (implicit ACK)
  - ON lead probe ("Status check"): Respond with status, then retry your report ONCE
  After 1 retry without ACK: approve shutdown regardless (heartbeat handles final recovery).
NEVER read ~/.claude/ files. NEVER use sleep loops. Messages arrive automatically.

CONTEXT:
{businessAnswers}
{IF storage_mode == "linear":}
LINEAR STATUS MAP (use UUIDs for update_issue state parameter, NOT string names):
{FOR name, uuid IN status_cache: "  {name} = {uuid}"}
{ENDIF}
```

## Stage 1: Validation (ln-310)

```
You are a pipeline worker in team "pipeline-{date}".
THINKING: Always enabled (adaptive). Reasoning effort: medium.
- Think adequately. Balance speed and thoroughness. Focus on core path.
Your assignment: Story {storyId} "{storyTitle}"

GIT CONTEXT: Worker self-detects branch via `git branch --show-current`.
If on feature/* branch — work here (ln-1000 creates worktree before spawning workers).
PIPELINE_DIR: {pipeline_dir}
ALL .pipeline/ file operations (checkpoint, done.flag) use PIPELINE_DIR (absolute path).

TASK: Execute Stage 1 — Story Validation.

Step 1: Invoke validation:
  Skill(skill: "ln-310-multi-agent-validator", args: "{storyId}")

Step 2: After ln-310 completes, check result:
  - If GO (Readiness >= 5, Penalty = 0): Report success to lead
  - If NO-GO: Report failure with reason to lead

Step 2b: Extract agent review info + write stage notes:
  Agent info extraction:
  - Look for "Agent Review:" display line in ln-310 output (e.g., "Agent Review: codex (2/3), gemini (1/2)")
  - OR read last entry from .agent-review/review_history.md
  - Format as agents_info: "codex(2/3),gemini(1/2)" or "SKIPPED({reason})"
  - If no agent info found: agents_info = "SKIPPED(unknown)"
  Write {PIPELINE_DIR}/stage_1_notes_{storyId}.md:
  ## Validation
  **Skill:** ln-310
  **Agent Review:** {agents_info}
  ### Key Decisions
  - {1-3 bullets: penalty points found/fixed, standards applied, agent findings accepted/rejected with reason}
  ### Artifacts
  - {Linear validation comment URL or file path}
  - {.agent-review/ result files if agents were used}

Step 3: Write checkpoint:
  Write {PIPELINE_DIR}/checkpoint-{storyId}.json with:
    stage=1, tasksCompleted=[], tasksRemaining=[],
    readiness={score from ln-310 (1-10)}, verdict={GO or NO-GO},
    reason={reason if NO-GO, omit if GO}

Step 4: Report to lead (use EXACT format per verdict):
  IF GO:
    SendMessage(type: "message", recipient: "pipeline-lead",
      content: "Stage 1 COMPLETE for {storyId}. Verdict: GO. Readiness: {score}. Agents: {agents_info}.",
      summary: "{storyId} Stage 1 GO")
  IF NO-GO:
    SendMessage(type: "message", recipient: "pipeline-lead",
      content: "Stage 1 COMPLETE for {storyId}. Verdict: NO-GO. Readiness: {score}. Reason: {reason}. Agents: {agents_info}.",
      summary: "{storyId} Stage 1 NO-GO")
Step 5: Wait for ACK from lead:
  Lead will send "ACK Stage 1 for {storyId}" after processing your report.
  - ON ACK received: Write {PIPELINE_DIR}/worker-{workerName}-done.flag -> approve next shutdown_request
  - ON shutdown_request (no explicit ACK): Write done.flag -> approve (implicit ACK)
  - ON lead probe ("Status check"): Respond with status, then retry your report ONCE
  After 1 retry without ACK: approve shutdown regardless (heartbeat handles final recovery).
NEVER read ~/.claude/ files. NEVER use sleep loops. Messages arrive automatically.

CONTEXT:
{businessAnswers}
{IF storage_mode == "linear":}
LINEAR STATUS MAP (use UUIDs for update_issue state parameter, NOT string names):
{FOR name, uuid IN status_cache: "  {name} = {uuid}"}
{ENDIF}
```

## Stage 2: Execution (ln-400)

```
You are a pipeline worker in team "pipeline-{date}".
THINKING: Always enabled (adaptive). Reasoning effort: medium.
- Think adequately. Balance speed and thoroughness. Focus on core path.
Your assignment: Story {storyId} "{storyTitle}"

GIT CONTEXT: Worker self-detects branch via `git branch --show-current`.
If on feature/* branch — work here (ln-1000 creates worktree before spawning workers).
PIPELINE_DIR: {pipeline_dir}
ALL .pipeline/ file operations (checkpoint, done.flag) use PIPELINE_DIR (absolute path).

MCP TOOL PREFERENCES (code editing only):
When mcp__hashline-edit__* tools are available (check via ToolSearch "+hashline-edit"),
prefer them over standard file tools for CODE files (.ts, .py, .js, .go, etc.):
- Read -> mcp__hashline-edit__read_file (hash-prefixed lines enable verified edits)
- Edit -> mcp__hashline-edit__edit_file (atomic, hash-verified, batch edits)
- Grep -> mcp__hashline-edit__grep (results include LINE:HASH for direct editing)
- Write -> mcp__hashline-edit__write_file (new files or full rewrites)
DO NOT use hashline-edit for: JSON configs, small YAML, markdown docs (overkill).
Fallback: if hashline-edit unavailable, use standard tools. No error.

TASK: Execute Stage 2 — Story Execution.

Step 1: Invoke executor:
  Skill(skill: "ln-400-story-executor", args: "{storyId}")

  CHECKPOINT: After EACH task completes within ln-400, update checkpoint:
    Write {PIPELINE_DIR}/checkpoint-{storyId}.json with stage=2,
    move completed task ID from tasksRemaining to tasksCompleted

Step 2: After ln-400 completes, check result:
  - All tasks Done, Story = To Review: Report success (Step 4a)
  - Any task stuck or error: Report error (Step 4b)

Step 2b: Write stage notes to {PIPELINE_DIR}/stage_2_notes_{storyId}.md:
  ## Implementation
  **Skill:** ln-400
  ### Key Decisions
  - {1-3 bullets: technical choices (library, pattern, architecture), challenges encountered and how resolved}
  ### Artifacts
  - {Git commit SHAs from this stage: `git log --oneline origin/{base_branch}..HEAD`}

Step 3: Write final checkpoint:
  Write {PIPELINE_DIR}/checkpoint-{storyId}.json with stage=2, all tasks in tasksCompleted

Step 4a: Report SUCCESS to lead:
  SendMessage(type: "message", recipient: "pipeline-lead",
    content: "Stage 2 COMPLETE for {storyId}. All tasks Done. Story set to To Review.",
    summary: "{storyId} Stage 2 Done")
Step 4b: Report ERROR to lead (if Step 2 failed):
  SendMessage(type: "message", recipient: "pipeline-lead",
    content: "Stage 2 ERROR for {storyId}: {details}",
    summary: "{storyId} Stage 2 ERROR")
Step 5: Wait for ACK from lead:
  Lead will send "ACK Stage 2 for {storyId}" after processing your report.
  - ON ACK received: Write {PIPELINE_DIR}/worker-{workerName}-done.flag -> approve next shutdown_request
  - ON shutdown_request (no explicit ACK): Write done.flag -> approve (implicit ACK)
  - ON lead probe ("Status check"): Respond with status, then retry your report ONCE
  After 1 retry without ACK: approve shutdown regardless (heartbeat handles final recovery).
NEVER read ~/.claude/ files. NEVER use sleep loops. Messages arrive automatically.

CONTEXT:
{businessAnswers}
{IF storage_mode == "linear":}
LINEAR STATUS MAP (use UUIDs for update_issue state parameter, NOT string names):
{FOR name, uuid IN status_cache: "  {name} = {uuid}"}
{ENDIF}
```

## Stage 3: Quality Gate (ln-500)

```
You are a pipeline worker in team "pipeline-{date}".
THINKING: Always enabled (adaptive). Reasoning effort: medium.
- Think adequately. Checklist-based quality checks — systematic verification, not creative analysis.
Your assignment: Story {storyId} "{storyTitle}"

GIT CONTEXT: Worker self-detects branch via `git branch --show-current`.
If on feature/* branch — work here (ln-1000 creates worktree before spawning workers).
PIPELINE_DIR: {pipeline_dir}
ALL .pipeline/ file operations (checkpoint, done.flag) use PIPELINE_DIR (absolute path).

TASK: Execute Stage 3 — Quality Gate.

Step 1: Invoke quality gate:
  Skill(skill: "ln-500-story-quality-gate", args: "{storyId}")

Step 2: After ln-500 completes, check verdict:
  - PASS: Report success with Quality Score
  - CONCERNS: Report success with notes
  - FAIL: Report failure with issues list
  - WAIVED: Report success with waiver reason

Step 2b: Extract agent review info + write stage notes:
  Agent info extraction:
  - Look for "Agent Review:" display line in ln-500/ln-510 output
  - OR read last entry from .agent-review/review_history.md
  - If FAST_TRACK=true and no agent review output: agents_info = "SKIPPED(fast-track)"
  - Format: "codex(2/3),gemini(1/2)" or "SKIPPED({reason})"
  - If no agent info found: agents_info = "SKIPPED(unknown)"
  Write {PIPELINE_DIR}/stage_3_notes_{storyId}.md:
  ## Quality Gate
  **Skill:** ln-500
  **Agent Review:** {agents_info}
  ### Key Decisions
  - {1-3 bullets: quality issues found/fixed, code review findings, branch finalization details}
  ### Artifacts
  - {Linear quality comment URL or file path}
  - {.agent-review/ result files if agents were used}
  - Branch: {branch_name}, git stats: {files_changed} files, +{lines_added}/-{lines_deleted}

Step 3: Write checkpoint:
  Write {PIPELINE_DIR}/checkpoint-{storyId}.json with:
    stage=3, all tasks in tasksCompleted,
    verdict={PASS/CONCERNS/WAIVED/FAIL from ln-500}, qualityScore={score from ln-500 (0-100)},
    issues={issues if FAIL, omit otherwise}

Step 4: Report to lead (use EXACT format per verdict):
  IF PASS/CONCERNS/WAIVED:
    SendMessage(type: "message", recipient: "pipeline-lead",
      content: "Stage 3 COMPLETE for {storyId}. Verdict: {PASS|CONCERNS|WAIVED}. Quality Score: {score}/100. Agents: {agents_info}.",
      summary: "{storyId} Stage 3 {verdict}")
  IF FAIL:
    SendMessage(type: "message", recipient: "pipeline-lead",
      content: "Stage 3 COMPLETE for {storyId}. Verdict: FAIL. Quality Score: {score}/100. Issues: {issues list}. Agents: {agents_info}.",
      summary: "{storyId} Stage 3 FAIL")
Step 5: Wait for ACK from lead:
  Lead will send "ACK Stage 3 for {storyId}" after processing your report.
  - ON ACK received: Write {PIPELINE_DIR}/worker-{workerName}-done.flag -> approve next shutdown_request
  - ON shutdown_request (no explicit ACK): Write done.flag -> approve (implicit ACK)
  - ON lead probe ("Status check"): Respond with status, then retry your report ONCE
  After 1 retry without ACK: approve shutdown regardless (heartbeat handles final recovery).
NEVER read ~/.claude/ files. NEVER use sleep loops. Messages arrive automatically.

CONTEXT:
{businessAnswers}
READINESS_SCORE: {readiness_scores[storyId] or "unknown"}
FAST_TRACK: {"true" IF readiness_scores[storyId] == 10 ELSE "false"}
{IF storage_mode == "linear":}
LINEAR STATUS MAP (use UUIDs for update_issue state parameter, NOT string names):
{FOR name, uuid IN status_cache: "  {name} = {uuid}"}
{ENDIF}
```

## Plan-Only Worker Templates

Plan-only workers: read-only analysis, no Skill()/file changes, SendMessage protocol.

### Plan Worker Spawn

```
Task(
  name: "story-{storyId}-s{stage}-plan",
  team_name: "pipeline-{date}",
  model: "opus",
  mode: "bypassPermissions",
  subagent_type: "general-purpose",
  prompt: plan_only_template(story, stage, business_answers)
)
```

### Per-Stage Variables

| Variable | Stage 0 | Stage 1 | Stage 2 | Stage 3 |
|----------|---------|---------|---------|---------|
| `{effort}` | low | low | medium | low |
| `{task_description}` | Propose task decomposition. DO NOT create tasks | Propose validation plan. DO NOT run validation | Propose execution plan. DO NOT implement | Propose quality gate plan. DO NOT run QA |
| `{analysis_steps}` | 1. Read Story requirements 2. Scan codebase structure 3. Identify tasks (1-8) | 1. Read Story ACs and Tasks 2. Check AC→Task coverage 3. Identify validation risks | 1. Read all Tasks (ACs, notes) 2. Analyze codebase per task 3. Plan approach per task 4. Map file ownership | 1. Read git diff 2. Identify audit dimensions 3. Plan test commands 4. Review branch strategy |
| `{plan_json}` | `{"tasks_planned": N, "tasks": [{"title","goal","estimate"}], "execution_order": "...", "risks": [...]}` | `{"ac_coverage": [{"ac","tasks"}], "risks": [...], "strategy": "..."}` | `{"tasks": [{"id","approach","files"}], "file_ownership": {...}, "test_plan": "..."}` | `{"audit_dimensions": [...], "test_commands": [...], "branch_strategy": "..."}` |
| `{forbidden}` | invoke Skill(), create tasks, modify files, write to Linear/kanban | invoke Skill(), modify files, run validation, update Linear/kanban | invoke Skill(), write code, modify files, run tests, update Linear/kanban | invoke Skill(), run tests, modify files, push branches, update Linear/kanban |
| `{extra_context}` | *(empty)* | *(empty)* | *(empty)* | `READINESS_SCORE: {readiness_scores[storyId] or "unknown"}` |

### Parameterized Plan Template

```
You are a pipeline PLAN worker in team "pipeline-{date}".
THINKING: Always enabled (adaptive). Reasoning effort: {effort}.
Your assignment: Story {storyId} "{storyTitle}"

GIT CONTEXT: Worker self-detects branch via `git branch --show-current`.
If on feature/* branch — work here. PIPELINE_DIR: {pipeline_dir}

TASK: {task_description}

READ-ONLY ANALYSIS:
{analysis_steps}

Step 1: Send plan to lead:
  SendMessage(type: "message", recipient: "pipeline-lead",
    content: "PLAN_RESULT for Stage {stage}, Story {storyId}.\nPlan: {JSON plan}",
    summary: "{storyId} Stage {stage} plan")

  Plan JSON: {plan_json}

Step 2: Wait for lead response:
  - ON PLAN_APPROVE: Write {PIPELINE_DIR}/worker-{workerName}-done.flag -> approve shutdown
  - ON PLAN_REVISE: Incorporate feedback, re-send PLAN_RESULT with revised plan
NEVER read ~/.claude/ files. NEVER use sleep loops. Messages arrive automatically.

DO NOT: {forbidden}

CONTEXT:
{businessAnswers}
{extra_context}
```

## Worker Lifecycle

Each worker handles exactly ONE stage (or one plan). After reporting completion/error:
1. Lead sends shutdown_request
2. Worker approves shutdown immediately
3. Lead spawns fresh worker for next stage (if any)

Workers NEVER receive follow-up stage commands. One stage = one worker lifecycle.

**Why:** Long-lived workers accumulate conversation context across stages (validation + task executions + reviews). By Stage 3, context is exhausted. Fresh workers start with clean context containing only stage-specific minimum.

---
**Version:** 2.0.0
**Last Updated:** 2026-03-09
