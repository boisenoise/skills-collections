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
> **Note:** Stage names: 0=Task Planning, 1=Validation, 2=Implementation, 3=Quality Gate

### ON "Stage 0 COMPLETE for {id}. {N} tasks created. Plan score: {score}/4."

```
# VERIFY
Re-read kanban board
ASSERT tasks exist under Story {id}         # Guard: verify ln-300 output
ASSERT task count IN 1..8                   # Guard: reasonable task count
IF ANY ASSERT fails: story_state[id] = "PAUSED"; ESCALATE; CONTINUE
story_state[id] = "STAGE_1"
stage_timestamps[id].stage_0_end = now()
stage_timestamps[id].stage_1_start = now()
# Shutdown old worker, spawn fresh for Stage 1
# ACK: confirm receipt before shutdown
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 0 for {id}", summary: "{id} Stage 0 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
SendMessage(type: "shutdown_request", recipient: worker_map[id])
next_worker = "story-{id}-s1-plan"
Task(name: next_worker, team_name: "pipeline-{date}",
     model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",
     prompt: plan_only_template(story, 1, business_answers))
worker_map[id] = next_worker
plan_approved[id] = false
Write .pipeline/worker-{next_worker}-active.flag
story_results[id].stage0 = "{N} tasks, {score}/4"
```

### ON "Stage 0 ERROR for {id}: {details}"

```
story_state[id] = "PAUSED"
# ACK: confirm receipt before shutdown (prevents worker retry latency)
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 0 for {id}", summary: "{id} Stage 0 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
ESCALATE to user: "Cannot create tasks for Story {id}: {details}"
SendMessage(type: "shutdown_request", recipient: worker_map[id])
story_results[id].stage0 = "ERROR: {details}"
Append story report section to docs/tasks/reports/pipeline-{date}.md (PAUSED)
```

## Stage 1 Handlers (Validation)

### ON "Stage 1 COMPLETE for {id}. Verdict: GO. Readiness: {score}. Agents: {agents_info}."

```
# VERIFY
Re-read kanban board
ASSERT Story {id} status = Todo              # Guard: verify ln-310 output
ASSERT readiness_score >= 5                  # Guard: ln-310 should have set score >= 5 for GO
IF ANY ASSERT fails: story_state[id] = "PAUSED"; ESCALATE; CONTINUE
story_state[id] = "STAGE_2"
stage_timestamps[id].stage_1_end = now()
stage_timestamps[id].stage_2_start = now()
# Shutdown old worker, spawn fresh for Stage 2
# ACK: confirm receipt before shutdown
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 1 for {id}", summary: "{id} Stage 1 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
SendMessage(type: "shutdown_request", recipient: worker_map[id])
next_worker = "story-{id}-s2-plan"
Task(name: next_worker, team_name: "pipeline-{date}",
     model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",
     prompt: plan_only_template(story, 2, business_answers))
worker_map[id] = next_worker
plan_approved[id] = false
Write .pipeline/worker-{next_worker}-active.flag
story_results[id].stage1 = "GO, {score}"
story_results[id].stage1_agents = "{agents_info}"    # From Agents: field; "N/A" if absent
readiness_scores[id] = {score}            # Preserve for Stage 3 fast-track decision
```

### ON "Stage 1 COMPLETE for {id}. Verdict: NO-GO. Readiness: {score}. Reason: {reason}. Agents: {agents_info}."

```
validation_retries[id]++
# ACK: confirm receipt before shutdown (prevents worker retry latency)
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 1 for {id}", summary: "{id} Stage 1 ACK")
IF validation_retries[id] <= 1:
  # Shutdown old worker, spawn fresh for Stage 1 retry
  Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
  SendMessage(type: "shutdown_request", recipient: worker_map[id])
  next_worker = "story-{id}-s1-retry-plan"
  Task(name: next_worker, team_name: "pipeline-{date}",
       model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",
       prompt: plan_only_template(story, 1, business_answers))
  worker_map[id] = next_worker
  plan_approved[id] = false
  Write .pipeline/worker-{next_worker}-active.flag
ELSE:
  story_state[id] = "PAUSED"
  Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
  ESCALATE to user: "Story {id} failed validation twice: {reason}"
  SendMessage(type: "shutdown_request", recipient: worker_map[id])
  story_results[id].stage1 = "NO-GO, {score}, {reason} (retries exhausted)"
  Append story report section to docs/tasks/reports/pipeline-{date}.md (PAUSED)
```

## Stage 2 Handlers (Implementation)

### ON "Stage 2 ERROR for {id}: {details}"

```
story_state[id] = "PAUSED"
# ACK: confirm receipt before shutdown (prevents worker retry latency)
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 2 for {id}", summary: "{id} Stage 2 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
ESCALATE to user: "Story {id} execution failed: {details}"
SendMessage(type: "shutdown_request", recipient: worker_map[id])
story_results[id].stage2 = "ERROR: {details}"
Append story report section to docs/tasks/reports/pipeline-{date}.md (PAUSED)
```

### ON "Stage 2 COMPLETE for {id}. All tasks Done. Story set to To Review."

```
# VERIFY
Re-read kanban board
ASSERT Story {id} status = To Review         # Guard: verify ln-400 output
ASSERT all tasks status = Done               # Guard: ln-400 should have completed all tasks
ASSERT feature branch has commits: `git log origin/{base_branch}..HEAD --oneline | wc -l` > 0
IF ANY ASSERT fails: story_state[id] = "PAUSED"; ESCALATE; CONTINUE
story_state[id] = "STAGE_3"
stage_timestamps[id].stage_2_end = now()
stage_timestamps[id].stage_3_start = now()
# Shutdown old worker, spawn fresh for Stage 3
# ACK: confirm receipt before shutdown
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 2 for {id}", summary: "{id} Stage 2 ACK")
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
SendMessage(type: "shutdown_request", recipient: worker_map[id])
next_worker = "story-{id}-s3-plan"
Task(name: next_worker, team_name: "pipeline-{date}",
     model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",
     prompt: plan_only_template(story, 3, business_answers))
worker_map[id] = next_worker
plan_approved[id] = false
Write .pipeline/worker-{next_worker}-active.flag
story_results[id].stage2 = "Done"
```

## Stage 3 Handlers (Quality Gate)

### ON "Stage 3 COMPLETE for {id}. Verdict: PASS|CONCERNS|WAIVED. Quality Score: {score}/100. Agents: {agents_info}."

```
# ACK: confirm receipt before shutdown
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 3 for {id}", summary: "{id} Stage 3 ACK")
stage_timestamps[id].stage_3_end = now()
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
SendMessage(type: "shutdown_request", recipient: worker_map[id])
story_results[id].stage3 = "{verdict} {score}/100"
story_results[id].stage3_agents = "{agents_info}"    # From Agents: field; "N/A" if absent

# VERIFY (read-only — lead ASSERTs, ln-500 is sole kanban writer per §9)
Re-read kanban board
ASSERT Story {id} status = Done                     # ln-500 set this
ASSERT all tasks status = Done
ASSERT branch pushed: `git branch -r` contains feature branch
# Extract git_stats from stage notes (written by worker in .pipeline/)
IF .pipeline/stage_3_notes_{id}.md exists:
  Parse git stats (files_changed, lines_added, lines_deleted) from stage notes
  git_stats[id] = { files_changed, lines_added, lines_deleted }
  branch_name = extract branch name from stage notes or Phase 3.4 variable
ELSE:
  # Fallback: extract from git directly
  git_stats[id] = parse `git diff --stat origin/{base_branch}..HEAD`
  branch_name = `git branch --show-current`
IF ANY ASSERT fails: WARN user (non-blocking: story likely Done, verification incomplete)

story_state[id] = "DONE"
Update .pipeline/state.json
```

### ON "Stage 3 COMPLETE for {id}. Verdict: FAIL. Quality Score: {score}/100. Issues: {issues}. Agents: {agents_info}."

```
# VERIFY (read-only — lead ASSERTs, ln-500 is sole kanban writer per §9)
Re-read kanban board
ASSERT Story {id} status = To Rework        # ln-500 set this on FAIL

quality_cycles[id]++
# ACK: confirm receipt before shutdown (prevents worker retry latency)
SendMessage(recipient: worker_map[id],
  content: "ACK Stage 3 for {id}", summary: "{id} Stage 3 ACK")
stage_timestamps[id].stage_3_end = now()
IF quality_cycles[id] < 2:
  previous_quality_score[id] = {score}          # Save for rework comparison on next FAIL
  story_state[id] = "STAGE_2"
  stage_timestamps[id].stage_2_start = now()    # Rework: restart Stage 2 timer
  # Shutdown old worker, spawn fresh for Stage 2 re-entry (fix tasks)
  Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
  SendMessage(type: "shutdown_request", recipient: worker_map[id])
  next_worker = "story-{id}-s2-fix{quality_cycles[id]}-plan"
  Task(name: next_worker, team_name: "pipeline-{date}",
       model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",
       prompt: plan_only_template(story, 2, business_answers))
  worker_map[id] = next_worker
  plan_approved[id] = false
  Write .pipeline/worker-{next_worker}-active.flag
ELSE:
  # Score comparison: detect rework degradation (autoresearch pattern)
  prev = previous_quality_score[id] OR null
  IF prev != null:
    delta = {score} - prev
    noise = "(within noise margin)" IF abs(delta) < 5 ELSE ""
    IF {score} < prev:
      escalation_msg = "Rework DEGRADED quality ({prev} → {score}) {noise}. Consider reverting."
    ELSE:
      escalation_msg = "Rework insufficient ({prev} → {score}) {noise}. Manual review needed."
  ELSE:
    escalation_msg = "Failed quality gate {quality_cycles[id]} times."
  story_state[id] = "PAUSED"
  Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
  ESCALATE to user: "Story {id}: {escalation_msg}"
  SendMessage(type: "shutdown_request", recipient: worker_map[id])
  story_results[id].stage3 = "FAIL {score}/100 (cycles exhausted, {escalation_msg})"
  Append story report section to docs/tasks/reports/pipeline-{date}.md (PAUSED)
```

## Plan Gate Handler

### ON "PLAN_RESULT for Stage {N}, Story {id}."

**MANDATORY READ:** Load `references/plan_gate_criteria.md` for auto-approval criteria per stage.

Handles plan submissions from plan-only workers.

```
# SENDER VALIDATION + STATE GUARD (same as execute workers)
VERIFY message.sender == worker_map[id]
IF story_state[id] != "STAGE_{N}": LOG "State mismatch"; re-send ACK; SKIP

# Parse plan JSON from message content (after "Plan: " prefix)
plan = parse_json(message.content.after("Plan: "))

# Evaluate against criteria (per plan_gate_criteria.md)
criteria_result = evaluate_plan_criteria(plan, N)

IF criteria_result.pass:
  # Approve plan — plan worker will write done.flag and shut down
  SendMessage(recipient: worker_map[id],
    content: "PLAN_APPROVE for Stage {N}, Story {id}. Proceed with execution.",
    summary: "{id} Stage {N} plan approved")
  OUTPUT: "Stage {N} plan approved: {criteria_result.summary}"

  # Wait for plan worker shutdown (done.flag + shutdown), then spawn execute worker
  # Execute worker spawn happens on next heartbeat after plan worker done.flag detected
  plan_approved[id] = true    # Flag for heartbeat to spawn execute worker

ELSE IF plan_revision_count[N] < 2:
  plan_revision_count[N]++
  SendMessage(recipient: worker_map[id],
    content: "PLAN_REVISE for Stage {N}, Story {id}. Feedback: {criteria_result.failures}. Revision {plan_revision_count[N]}/2.",
    summary: "{id} Stage {N} plan revise")
  OUTPUT: "Stage {N} plan needs revision ({plan_revision_count[N]}/2): {criteria_result.failures}"

ELSE:
  # Plan rejected — exhausted revisions
  SendMessage(recipient: worker_map[id],
    content: "ACK Stage {N} for {id}", summary: "{id} Stage {N} ACK")
  Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
  SendMessage(type: "shutdown_request", recipient: worker_map[id])
  story_state[id] = "PAUSED"
  ESCALATE: "Plan rejected 2 times for Stage {N}, Story {id}"
  story_results[id]["stage{N}_plan"] = "REJECTED (2 revisions exhausted)"

Write .pipeline/state.json
```

### Plan Worker Done-Flag Detection (in heartbeat)

When `plan_approved[id] == true` and plan worker's done.flag exists:
```
# Plan worker has shut down after APPROVE — spawn execute worker
Bash: rm -f .pipeline/worker-{worker_map[id]}-active.flag .pipeline/worker-{worker_map[id]}-done.flag
execute_worker = "story-{id}-s{N}"
Task(name: execute_worker, team_name: "pipeline-{date}",
     model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",
     prompt: worker_prompt(story, N, business_answers))
worker_map[id] = execute_worker
Write .pipeline/worker-{execute_worker}-active.flag
plan_approved[id] = false
```

## Crash Detection Handler

### ON worker TeammateIdle WITHOUT prior completion message for {id}

3-step crash detection protocol (see worker_health_contract.md):

```
# Step 1: Flag suspicious
suspicious_idle = true

# Step 2: Probe
SendMessage(recipient: worker_map[id],
            content: "Status check: are you still working on Stage {N} for {id}?",
            summary: "{id} health check")

# Step 3: Evaluate
ON worker responds with parseable status:
  suspicious_idle = false                # False alarm, continue

ON TeammateIdle again WITHOUT response:
  crash_count[id]++
  IF crash_count[id] <= 1:
    # Resume protocol (see checkpoint_format.md):
    checkpoint = read(".pipeline/checkpoint-{id}.json")
    IF checkpoint.agentId exists:
      Task(resume: checkpoint.agentId)          # Try 1: full context resume
      # worker_map[id] remains unchanged (same agent, resumed)
    ELSE:
      next_worker = "story-{id}-s{checkpoint.stage}-retry"
      new_prompt = worker_prompt(story, checkpoint.stage, business_answers) + CHECKPOINT_RESUME block
      Task(name: next_worker, team_name: "pipeline-{date}",
           model: "opus", mode: "bypassPermissions", subagent_type: "general-purpose",
           prompt: new_prompt)                  # Try 2: Opus for crash recovery/troubleshooting
      worker_map[id] = next_worker
  ELSE:
    story_state[id] = "PAUSED"
    ESCALATE: "Story {id} worker crashed twice at Stage {N}"
    story_results[id].crash = "Crashed at Stage {N} (crash_count={crash_count[id]})"
```

## Related Files

- **Heartbeat & Active Verification:** `phase4_heartbeat.md`
- **Health Contract:** `worker_health_contract.md`
- **Checkpoint Format:** `checkpoint_format.md`

---
**Version:** 2.0.0
**Last Updated:** 2026-03-09
