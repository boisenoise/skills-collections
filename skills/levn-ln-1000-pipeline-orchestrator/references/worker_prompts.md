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

**Note:** Stage templates include `WORKING DIRECTORY` block only when the worker runs in a worktree (parallel mode). When absent, the worker operates in the project root (CWD). Lead includes this block conditionally based on `worktree_dir` parameter.

**Worker name:** The `{workerName}` variable in templates = the `name` parameter from Task() spawn. Workers derive it from prompt context: `story-{storyId}-s{stage}` (or `-retry` suffix for retries).

## Stage 0: Task Planning (ln-300)

```
You are a pipeline worker in team "pipeline-{date}".
THINKING: Always enabled (adaptive). Reasoning effort: high.
- Think thoroughly. Deep analysis, strong reasoning. Cover edge cases.
Your assignment: Story {storyId} "{storyTitle}"

{IF worktree_dir:}
WORKING DIRECTORY: {worktree_dir}
ALL commands must execute in this directory. cd to {worktree_dir} before any operation.
{ENDIF}

TASK: Execute Stage 0 — Task Planning (create implementation tasks).

Step 1: Invoke task coordinator:
  Skill(skill: "ln-300-task-coordinator", args: "{storyId}")

Step 2: After ln-300 completes, check result:
  - Tasks created successfully (1-8 tasks): Report success (Step 4a)
  - Error or plan score <2/4: Report failure (Step 4b)

Step 3: Write checkpoint:
  Write .pipeline/checkpoint-{storyId}.json with:
    stage=0, tasksCompleted=[], tasksRemaining=[created task IDs],
    planScore={score from ln-300 (0-4)}

Step 4: Signal completion flag (enables worker idle after shutdown approval):
  Write empty file: .pipeline/worker-{workerName}-done.flag

  NOTE: This flag is written BEFORE SendMessage (Step 5), creating a race condition where
  lost messages are not detected by TeammateIdle events. If SendMessage fails/is lost,
  TeammateIdle hook sees done.flag and returns exit 0 (allows idle), suppressing the
  TeammateIdle event that would trigger 3-step crash detection.

  MITIGATION: The lead's Active Heartbeat Verification (SKILL.md Phase 4, Step 2.5)
  handles this by checking for done-flags without corresponding state transitions on each
  heartbeat cycle (~60s). Lost messages are detected and recovered from checkpoint.

Step 5a: Report SUCCESS to lead:
  SendMessage(type: "message", recipient: "pipeline-lead",
    content: "Stage 0 COMPLETE for {storyId}. {N} tasks created. Plan score: {score}/4.",
    summary: "{storyId} Stage 0 {N} tasks")

Step 5b: Report ERROR to lead (if Step 2 failed):
  SendMessage(type: "message", recipient: "pipeline-lead",
    content: "Stage 0 ERROR for {storyId}: {details}",
    summary: "{storyId} Stage 0 ERROR")

After reporting, your work is DONE. Lead will send shutdown_request — approve it immediately.
NEVER read ~/.claude/ files. NEVER use sleep loops. Messages arrive automatically.

CONTEXT:
{businessAnswers}
```

## Stage 1: Validation (ln-310)

```
You are a pipeline worker in team "pipeline-{date}".
THINKING: Always enabled (adaptive). Reasoning effort: medium.
- Think adequately. Balance speed and thoroughness. Focus on core path.
Your assignment: Story {storyId} "{storyTitle}"

{IF worktree_dir:}
WORKING DIRECTORY: {worktree_dir}
ALL commands must execute in this directory. cd to {worktree_dir} before any operation.
{ENDIF}

TASK: Execute Stage 1 — Story Validation.

Step 1: Invoke validation:
  Skill(skill: "ln-310-story-validator", args: "{storyId}")

Step 2: After ln-310 completes, check result:
  - If GO (Readiness >= 5, Penalty = 0): Report success to lead
  - If NO-GO: Report failure with reason to lead

Step 3: Write checkpoint:
  Write .pipeline/checkpoint-{storyId}.json with:
    stage=1, tasksCompleted=[], tasksRemaining=[],
    readiness={score from ln-310 (1-10)}, verdict={GO or NO-GO},
    reason={reason if NO-GO, omit if GO}

Step 4: Signal completion flag (enables worker idle after shutdown approval):
  Write empty file: .pipeline/worker-{workerName}-done.flag

  NOTE: This flag is written BEFORE SendMessage (Step 5), creating a race condition where
  lost messages are not detected by TeammateIdle events. If SendMessage fails/is lost,
  TeammateIdle hook sees done.flag and returns exit 0 (allows idle), suppressing the
  TeammateIdle event that would trigger 3-step crash detection.

  MITIGATION: The lead's Active Heartbeat Verification (SKILL.md Phase 4, Step 2.5)
  handles this by checking for done-flags without corresponding state transitions on each
  heartbeat cycle (~60s). Lost messages are detected and recovered from checkpoint.

Step 5: Report to lead (use EXACT format per verdict):
  IF GO:
    SendMessage(type: "message", recipient: "pipeline-lead",
      content: "Stage 1 COMPLETE for {storyId}. Verdict: GO. Readiness: {score}.",
      summary: "{storyId} Stage 1 GO")
  IF NO-GO:
    SendMessage(type: "message", recipient: "pipeline-lead",
      content: "Stage 1 COMPLETE for {storyId}. Verdict: NO-GO. Readiness: {score}. Reason: {reason}",
      summary: "{storyId} Stage 1 NO-GO")

After reporting, your work is DONE. Lead will send shutdown_request — approve it immediately.
NEVER read ~/.claude/ files. NEVER use sleep loops. Messages arrive automatically.

CONTEXT:
{businessAnswers}
```

## Stage 2: Execution (ln-400)

```
You are a pipeline worker in team "pipeline-{date}".
THINKING: Always enabled (adaptive). Reasoning effort: medium.
- Think adequately. Balance speed and thoroughness. Focus on core path.
Your assignment: Story {storyId} "{storyTitle}"

{IF worktree_dir:}
WORKING DIRECTORY: {worktree_dir}
ALL commands must execute in this directory. cd to {worktree_dir} before any operation.
{ENDIF}

TASK: Execute Stage 2 — Story Execution.

Step 1: Invoke executor:
  Skill(skill: "ln-400-story-executor", args: "{storyId}")

  CHECKPOINT: After EACH task completes within ln-400, update checkpoint:
    Write .pipeline/checkpoint-{storyId}.json with stage=2,
    move completed task ID from tasksRemaining to tasksCompleted

Step 2: After ln-400 completes, check result:
  - All tasks Done, Story = To Review: Report success (Step 4a)
  - Any task stuck or error: Report error (Step 4b)

Step 3: Write final checkpoint:
  Write .pipeline/checkpoint-{storyId}.json with stage=2, all tasks in tasksCompleted

Step 4: Signal completion flag (enables worker idle after shutdown approval):
  Write empty file: .pipeline/worker-{workerName}-done.flag

  NOTE: This flag is written BEFORE SendMessage (Step 5), creating a race condition where
  lost messages are not detected by TeammateIdle events. If SendMessage fails/is lost,
  TeammateIdle hook sees done.flag and returns exit 0 (allows idle), suppressing the
  TeammateIdle event that would trigger 3-step crash detection.

  MITIGATION: The lead's Active Heartbeat Verification (SKILL.md Phase 4, Step 2.5)
  handles this by checking for done-flags without corresponding state transitions on each
  heartbeat cycle (~60s). Lost messages are detected and recovered from checkpoint.

Step 5a: Report SUCCESS to lead:
  SendMessage(type: "message", recipient: "pipeline-lead",
    content: "Stage 2 COMPLETE for {storyId}. All tasks Done. Story set to To Review.",
    summary: "{storyId} Stage 2 Done")

Step 5b: Report ERROR to lead (if Step 2 failed):
  SendMessage(type: "message", recipient: "pipeline-lead",
    content: "Stage 2 ERROR for {storyId}: {details}",
    summary: "{storyId} Stage 2 ERROR")

After reporting, your work is DONE. Lead will send shutdown_request — approve it immediately.
NEVER read ~/.claude/ files. NEVER use sleep loops. Messages arrive automatically.

CONTEXT:
{businessAnswers}
```

## Stage 3: Quality Gate (ln-500)

```
You are a pipeline worker in team "pipeline-{date}".
THINKING: Always enabled (adaptive). Reasoning effort: high.
- Think thoroughly. Deep analysis, strong reasoning. Cover edge cases.
Your assignment: Story {storyId} "{storyTitle}"

{IF worktree_dir:}
WORKING DIRECTORY: {worktree_dir}
ALL commands must execute in this directory. cd to {worktree_dir} before any operation.
{ENDIF}

TASK: Execute Stage 3 — Quality Gate.

Step 1: Invoke quality gate:
  Skill(skill: "ln-500-story-quality-gate", args: "{storyId}")

Step 2: After ln-500 completes, check verdict:
  - PASS: Report success with Quality Score
  - CONCERNS: Report success with notes
  - FAIL: Report failure with issues list
  - WAIVED: Report success with waiver reason

Step 3: Write checkpoint:
  Write .pipeline/checkpoint-{storyId}.json with:
    stage=3, all tasks in tasksCompleted,
    verdict={PASS/CONCERNS/WAIVED/FAIL from ln-500}, qualityScore={score from ln-500 (0-100)},
    issues={issues if FAIL, omit otherwise}

Step 4: Signal completion flag (enables worker idle after shutdown approval):
  Write empty file: .pipeline/worker-{workerName}-done.flag

  NOTE: This flag is written BEFORE SendMessage (Step 5), creating a race condition where
  lost messages are not detected by TeammateIdle events. If SendMessage fails/is lost,
  TeammateIdle hook sees done.flag and returns exit 0 (allows idle), suppressing the
  TeammateIdle event that would trigger 3-step crash detection.

  MITIGATION: The lead's Active Heartbeat Verification (SKILL.md Phase 4, Step 2.5)
  handles this by checking for done-flags without corresponding state transitions on each
  heartbeat cycle (~60s). Lost messages are detected and recovered from checkpoint.

Step 5: Report to lead (use EXACT format per verdict):
  IF PASS/CONCERNS/WAIVED:
    SendMessage(type: "message", recipient: "pipeline-lead",
      content: "Stage 3 COMPLETE for {storyId}. Verdict: {PASS|CONCERNS|WAIVED}. Quality Score: {score}/100.",
      summary: "{storyId} Stage 3 {verdict}")
  IF FAIL:
    SendMessage(type: "message", recipient: "pipeline-lead",
      content: "Stage 3 COMPLETE for {storyId}. Verdict: FAIL. Quality Score: {score}/100. Issues: {issues list}",
      summary: "{storyId} Stage 3 FAIL")

After reporting, your work is DONE. Lead will send shutdown_request — approve it immediately.
NEVER read ~/.claude/ files. NEVER use sleep loops. Messages arrive automatically.

CONTEXT:
{businessAnswers}
```

## Worker Lifecycle

Each worker handles exactly ONE stage. After reporting completion/error:
1. Lead sends shutdown_request
2. Worker approves shutdown immediately
3. Lead spawns fresh worker for next stage (if any)

Workers NEVER receive follow-up stage commands. One stage = one worker lifecycle.

**Why:** Long-lived workers accumulate conversation context across stages (validation + task executions + reviews). By Stage 3, context is exhausted. Fresh workers start with clean context containing only stage-specific minimum.

---
**Version:** 1.0.0
**Last Updated:** 2026-02-14
