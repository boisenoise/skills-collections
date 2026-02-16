# Phase 4: Message Handlers

Message processing logic for worker completion/error messages. All handlers include sender validation and state guards to prevent duplicate processing.

## Message Processing Rules

Messages from workers arrive as conversation context in each heartbeat iteration. Match against ON handlers below. If no match → ON NO NEW MESSAGES (see phase4_heartbeat.md).

### SENDER VALIDATION

Before processing ANY completion message, verify sender:
```
VERIFY message.sender == worker_map[id]
IF mismatch: LOG "Ignoring stale message from {sender} for {id}"; SKIP handler
```
This prevents old/dead workers from corrupting pipeline state.

### STATE GUARD

Before processing ANY stage completion, verify story is in expected state:
- Stage 0 COMPLETE → story_state[id] must be "STAGE_0"
- Stage 1 COMPLETE → story_state[id] must be "STAGE_1"
- Stage 2 COMPLETE → story_state[id] must be "STAGE_2"
- Stage 3 COMPLETE → story_state[id] must be "STAGE_3"

```
IF mismatch:
  # Duplicate — re-send ACK (worker may be retrying), do NOT reprocess
  SendMessage(recipient: worker_map[id],
    content: "ACK Stage {N} for {id}", summary: "{id} ACK (dup)")
  LOG "Duplicate/stale message for {id} (state={story_state[id]})"; SKIP handler
```
This prevents double-spawn when same completion message is delivered across heartbeats. Re-sending ACK ensures retrying workers get confirmation.

## Stage 0 Handlers (Task Planning)

### ON "Stage 0 COMPLETE for {id}. {N} tasks created. Plan score: {score}/4."

```
Re-read kanban board
ASSERT tasks exist under Story {id}         # Guard: verify ln-300 output
IF tasks missing: story_state[id] = "PAUSED"; ESCALATE; CONTINUE
story_state[id] = "STAGE_1"
stage_timestamps[id].stage_0_end = now()
stage_timestamps[id].stage_1_start = now()
# Shutdown old worker, spawn fresh for Stage 1
# ACK: confirm receipt before shutdown
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 0 for {id}", summary: "{id} Stage 0 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
SendMessage(type: "shutdown_request", recipient: worker_map[id])
next_worker = "story-{id}-s1"
Task(name: next_worker, team_name: "pipeline-{date}",
     model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",
     prompt: worker_prompt(story, 1, business_answers, worktree_map[id], project_root))
worker_map[id] = next_worker
Write .pipeline/worker-{next_worker}-active.flag
story_results[id].stage0 = "{N} tasks, {score}/4"
```

### ON "Stage 0 ERROR for {id}: {details}"

```
story_state[id] = "PAUSED"
active_workers--
# ACK: confirm receipt before shutdown (prevents worker retry latency)
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 0 for {id}", summary: "{id} Stage 0 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
Bash: git worktree remove .worktrees/story-{id} --force
worktree_map[id] = null
ESCALATE to user: "Cannot create tasks for Story {id}: {details}"
SendMessage(type: "shutdown_request", recipient: worker_map[id])
story_results[id].stage0 = "ERROR: {details}"
Append story report section to docs/tasks/reports/pipeline-{date}.md (PAUSED)
```

## Stage 1 Handlers (Story Validation)

### ON "Stage 1 COMPLETE for {id}. Verdict: GO. Readiness: {score}."

```
Re-read kanban board
ASSERT Story {id} status = Todo              # Guard: verify ln-310 output
story_state[id] = "STAGE_2"
stage_timestamps[id].stage_1_end = now()
stage_timestamps[id].stage_2_start = now()
# Shutdown old worker, spawn fresh for Stage 2
# ACK: confirm receipt before shutdown
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 1 for {id}", summary: "{id} Stage 1 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
SendMessage(type: "shutdown_request", recipient: worker_map[id])
next_worker = "story-{id}-s2"
Task(name: next_worker, team_name: "pipeline-{date}",
     model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",      # Stage 2 medium effort
     prompt: worker_prompt(story, 2, business_answers, worktree_map[id], project_root))
worker_map[id] = next_worker
Write .pipeline/worker-{next_worker}-active.flag
story_results[id].stage1 = "GO, {score}"
readiness_scores[id] = {score}            # Preserve for Stage 3 fast-track decision
```

### ON "Stage 1 COMPLETE for {id}. Verdict: NO-GO. Readiness: {score}. Reason: {reason}"

```
validation_retries[id]++
# ACK: confirm receipt before shutdown (prevents worker retry latency)
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 1 for {id}", summary: "{id} Stage 1 ACK")
IF validation_retries[id] <= 1:
  # Shutdown old worker, spawn fresh for Stage 1 retry
  Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
  SendMessage(type: "shutdown_request", recipient: worker_map[id])
  next_worker = "story-{id}-s1-retry"
  Task(name: next_worker, team_name: "pipeline-{date}",
       model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",    # Stage 1 = review
       prompt: worker_prompt(story, 1, business_answers, worktree_map[id], project_root))
  worker_map[id] = next_worker
  Write .pipeline/worker-{next_worker}-active.flag
ELSE:
  story_state[id] = "PAUSED"
  active_workers--
  Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
  Bash: git worktree remove .worktrees/story-{id} --force
  worktree_map[id] = null
  ESCALATE to user: "Story {id} failed validation twice: {reason}"
  SendMessage(type: "shutdown_request", recipient: worker_map[id])
  story_results[id].stage1 = "NO-GO, {score}, {reason} (retries exhausted)"
  Append story report section to docs/tasks/reports/pipeline-{date}.md (PAUSED)
```

## Stage 2 Handlers (Story Execution)

### ON "Stage 2 ERROR for {id}: {details}"

```
story_state[id] = "PAUSED"
active_workers--
# ACK: confirm receipt before shutdown (prevents worker retry latency)
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 2 for {id}", summary: "{id} Stage 2 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
Bash: git worktree remove .worktrees/story-{id} --force
worktree_map[id] = null
ESCALATE to user: "Story {id} execution failed: {details}"
SendMessage(type: "shutdown_request", recipient: worker_map[id])
story_results[id].stage2 = "ERROR: {details}"
Append story report section to docs/tasks/reports/pipeline-{date}.md (PAUSED)
```

### ON "Stage 2 COMPLETE for {id}. All tasks Done. Story set to To Review."

```
Re-read kanban board
ASSERT Story {id} status = To Review         # Guard: verify ln-400 output
story_state[id] = "STAGE_3"
stage_timestamps[id].stage_2_end = now()
stage_timestamps[id].stage_3_start = now()
# Shutdown old worker, spawn fresh for Stage 3
# ACK: confirm receipt before shutdown
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 2 for {id}", summary: "{id} Stage 2 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
SendMessage(type: "shutdown_request", recipient: worker_map[id])
next_worker = "story-{id}-s3"
Task(name: next_worker, team_name: "pipeline-{date}",
     model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",      # Stage 3 = QA
     prompt: worker_prompt(story, 3, business_answers, worktree_map[id], project_root))
worker_map[id] = next_worker
Write .pipeline/worker-{next_worker}-active.flag
story_results[id].stage2 = "Done"
```

## Stage 3 Handlers (Quality Gate)

### ON "Stage 3 COMPLETE for {id}. Verdict: PASS|CONCERNS|WAIVED. Quality Score: {score}/100."

```
# ACK: confirm receipt before shutdown
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 3 for {id}", summary: "{id} Stage 3 ACK")
stage_timestamps[id].stage_3_end = now()
active_workers--
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
SendMessage(type: "shutdown_request", recipient: worker_map[id])
# Squash merge BEFORE marking DONE (crash between merge and DONE = recoverable)
Squash merge (see phase4a_git_merge.md)
# Only set DONE after successful merge (phase4a sets PAUSED on conflict)
story_state[id] = "DONE"
Update kanban: Story → Done
Update .pipeline/state.json: active_workers, stories_remaining, last_check
story_results[id].stage3 = "{verdict} {score}/100"
```

### ON "Stage 3 COMPLETE for {id}. Verdict: FAIL. Quality Score: {score}/100. Issues: {issues}"

```
quality_cycles[id]++
# ACK: confirm receipt before shutdown (prevents worker retry latency)
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 3 for {id}", summary: "{id} Stage 3 ACK")
stage_timestamps[id].stage_3_end = now()
IF quality_cycles[id] < 2:
  story_state[id] = "STAGE_2"
  stage_timestamps[id].stage_2_start = now()    # Rework: restart Stage 2 timer
  # Shutdown old worker, spawn fresh for Stage 2 re-entry (fix tasks)
  Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
  SendMessage(type: "shutdown_request", recipient: worker_map[id])
  next_worker = "story-{id}-s2-fix{quality_cycles[id]}"
  Task(name: next_worker, team_name: "pipeline-{date}",
       model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",    # Stage 2 medium effort (fix)
       prompt: worker_prompt(story, 2, business_answers, worktree_map[id], project_root))
  worker_map[id] = next_worker
  Write .pipeline/worker-{next_worker}-active.flag
ELSE:
  story_state[id] = "PAUSED"
  active_workers--
  Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
  Bash: git worktree remove .worktrees/story-{id} --force
  worktree_map[id] = null
  ESCALATE to user: "Story {id} failed quality gate {quality_cycles[id]} times"
  SendMessage(type: "shutdown_request", recipient: worker_map[id])
  story_results[id].stage3 = "FAIL {score}/100 (cycles exhausted)"
  Append story report section to docs/tasks/reports/pipeline-{date}.md (PAUSED)
```

## Crash Detection Handler

### ON worker TeammateIdle WITHOUT prior completion message for {id}

3-step crash detection protocol (see worker_health_contract.md):

```
# Step 1: Flag suspicious
suspicious_idle[id] = true

# Step 2: Probe
SendMessage(recipient: worker_map[id],
            content: "Status check: are you still working on Stage {N} for {id}?",
            summary: "{id} health check")

# Step 3: Evaluate
ON worker responds with parseable status:
  suspicious_idle[id] = false           # False alarm, continue

ON TeammateIdle again WITHOUT response:
  crash_count[id]++
  IF crash_count[id] <= 1:
    active_workers--
    # Resume protocol (see checkpoint_format.md):
    checkpoint = read(".pipeline/checkpoint-{id}.json")
    IF checkpoint.agentId exists:
      Task(resume: checkpoint.agentId)          # Try 1: full context resume
    ELSE:
      new_prompt = worker_prompt(story, checkpoint.stage, business_answers, worktree_map[id], project_root) + CHECKPOINT_RESUME block
      Task(name: "story-{id}-s{checkpoint.stage}-retry", team_name: "pipeline-{date}",
           model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",
           prompt: new_prompt)                  # Try 2: Opus for crash recovery/troubleshooting
    worker_map[id] = new_worker_name
    active_workers++
  ELSE:
    story_state[id] = "PAUSED"
    active_workers--
    Bash: git worktree remove .worktrees/story-{id} --force
    worktree_map[id] = null
    ESCALATE: "Story {id} worker crashed twice at Stage {N}"
    story_results[id].crash = "Crashed at Stage {N} (crash_count={crash_count[id]})"
```

## Related Files

- **Heartbeat & Active Verification:** `phase4_heartbeat.md`
- **Git Flow:** `phase4a_git_merge.md`
- **Health Contract:** `worker_health_contract.md`
- **Checkpoint Format:** `checkpoint_format.md`

---
**Version:** 1.0.0
**Last Updated:** 2026-02-14
