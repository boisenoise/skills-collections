# Phase 4: Heartbeat & Active Verification

Bidirectional health monitoring combining reactive message processing (phase4_handlers.md) with proactive done-flag verification. Single Story mode — monitors one worker at a time.

## Context Recovery (Compression Detection)

When Claude Code compresses conversation history during long pipelines, the lead loses SKILL.md instructions and in-memory state. The Stop hook includes `---PIPELINE RECOVERY CONTEXT---` in every heartbeat to enable self-healing.

### Detection

Lead detects context loss when:
- It sees `---PIPELINE RECOVERY CONTEXT---` in heartbeat stderr
- It cannot recall pipeline state variables or ON handlers
- The recovery block contains inline compact state for immediate situational awareness

### Recovery Steps

1. **Read** `.pipeline/state.json` → restore ALL state variables including team_name, business_answers, storage_mode, selected_story_id
2. **Read** SKILL.md (FULL) → restore all phases, rules, error handling, anti-patterns
3. **Read** `references/phases/phase4_handlers.md` → restore all ON message handlers
4. **Read** `references/phases/phase4_heartbeat.md` → restore verification + heartbeat output
5. **Read** `references/known_issues.md` → restore self-diagnostic patterns
6. **Set** ephemeral variables: `suspicious_idle = false`, `heartbeat_count = 0`. Run `ToolSearch("+hashline-edit")` for MCP tools
7. **Resume** event loop: process messages → verify flags → persist state → end turn

### Token Cost

| Scenario | Files Read | Approx Tokens |
|----------|-----------|---------------|
| Normal heartbeat (no compression) | 0 | 0 |
| After compression (one-time recovery) | 4 files | ~2500 |
| Recovery block in stderr (every heartbeat) | -- | ~120 |

## Active Done-Flag Verification (Step 3)

Detects lost completion messages by checking for done-flags without state transitions. Complements reactive crash detection (ON TeammateIdle) with proactive polling every heartbeat cycle.

**Problem:** Worker creates `done.flag` before `SendMessage`. If message is lost (network, overflow, crash), TeammateIdle hook returns `exit 0`, suppressing TeammateIdle event. Reactive crash detection never triggers.

**Solution:** Proactive verification on each heartbeat checks for flags without corresponding state advancement.

### Algorithm

```
story_id = selected_story_id
IF story_state[story_id] NOT IN ["STAGE_0", "STAGE_1", "STAGE_2", "STAGE_3"]:
  SKIP    # Not in active stage

worker_name = worker_map[story_id]
done_flag_path = ".pipeline/worker-{worker_name}-done.flag"

IF exists(done_flag_path):
  # Worker signaled completion via flag, verify we received the message
  current_stage = extract_stage_number(story_state[story_id])  # STAGE_0 → 0, etc.

  # Determine expected state after completion
  next_expected_state = "STAGE_{current_stage + 1}" if current_stage < 3 else "PENDING_MERGE"

  # Check if state has advanced (message received and processed)
  state_advanced = (story_state[story_id] == next_expected_state) OR
                   (story_state[story_id] IN ("DONE", "PENDING_MERGE"))

  IF NOT state_advanced:
    # Lost message detected: flag exists but handler never ran
    Output: "Lost completion message for {story_id} at Stage {current_stage}. Attempting recovery from checkpoint..."

    checkpoint = read(".pipeline/checkpoint-{story_id}.json") if exists
    synthetic_recovery_successful = false

    IF checkpoint AND checkpoint.stage == current_stage:
      # Synthetic recovery based on checkpoint + kanban verification

      IF current_stage == 0:
        # Stage 0: Verify tasks created in kanban board
        Re-read kanban board
        tasks_exist = count_tasks_under_story(story_id) > 0
        IF tasks_exist:
          task_count = count_tasks_under_story(story_id)
          plan_score = checkpoint.planScore
          Output: "Recovered Stage 0 completion for {story_id}. {task_count} tasks created."
          CALL ON "Stage 0 COMPLETE for {story_id}. {task_count} tasks created. Plan score: {plan_score}/4."
          synthetic_recovery_successful = true
        ELSE:
          Output: "Stage 0 checkpoint invalid for {story_id}: tasks not found despite done.flag"
          CALL ON "Stage 0 ERROR for {story_id}: Tasks not found despite done.flag"
          synthetic_recovery_successful = true

      ELSE IF current_stage == 1:
        # Stage 1: Verify Story moved to Todo (GO) or still Backlog (NO-GO)
        Re-read kanban board
        story_status = get_story_status(story_id)
        IF story_status == "Todo":
          readiness = checkpoint.readiness
          Output: "Recovered Stage 1 completion for {story_id}. Verdict: GO."
          CALL ON "Stage 1 COMPLETE for {story_id}. Verdict: GO. Readiness: {readiness}."
          synthetic_recovery_successful = true
        ELSE:
          reason = checkpoint.reason
          readiness = checkpoint.readiness
          Output: "Recovered Stage 1 completion for {story_id}. Verdict: NO-GO."
          CALL ON "Stage 1 COMPLETE for {story_id}. Verdict: NO-GO. Readiness: {readiness}. Reason: {reason}"
          synthetic_recovery_successful = true

      ELSE IF current_stage == 2:
        # Stage 2: Verify Story moved to To Review
        Re-read kanban board
        story_status = get_story_status(story_id)
        IF story_status == "To Review":
          Output: "Recovered Stage 2 completion for {story_id}. Story in To Review."
          CALL ON "Stage 2 COMPLETE for {story_id}. All tasks Done. Story set to To Review."
          synthetic_recovery_successful = true
        ELSE:
          Output: "Stage 2 checkpoint invalid for {story_id}: Story not in To Review despite done.flag"
          CALL ON "Stage 2 ERROR for {story_id}: Story not in To Review despite done.flag"
          synthetic_recovery_successful = true

      ELSE IF current_stage == 3:
        # Stage 3: Verify verdict from checkpoint
        verdict = checkpoint.verdict
        score = checkpoint.qualityScore
        IF verdict in ["PASS", "CONCERNS", "WAIVED"]:
          Output: "Recovered Stage 3 completion for {story_id}. Verdict: {verdict}."
          CALL ON "Stage 3 COMPLETE for {story_id}. Verdict: {verdict}. Quality Score: {score}/100."
          synthetic_recovery_successful = true
        ELSE:
          issues = checkpoint.issues
          Output: "Recovered Stage 3 completion for {story_id}. Verdict: FAIL."
          CALL ON "Stage 3 COMPLETE for {story_id}. Verdict: FAIL. Quality Score: {score}/100. Issues: {issues}"
          synthetic_recovery_successful = true

    IF NOT synthetic_recovery_successful:
      # Checkpoint missing/invalid - fallback to probe protocol
      Output: "Cannot recover {story_id} from checkpoint. Sending diagnostic probe..."
      suspicious_idle = true
      SendMessage(recipient: worker_name,
                 content: "Status check: are you still working on Stage {current_stage} for {story_id}?",
                 summary: "{story_id} health check")
```

## Heartbeat State Persistence (Step 4)

```
ON HEARTBEAT (Stop hook stderr: "HEARTBEAT: ..."):
  Write .pipeline/state.json with ALL state variables:
    complete, selected_story_id,
    stories_remaining = (1 if story_state[selected_story_id] NOT IN ("DONE", "PAUSED") else 0),
    last_check=now,
    story_state, worker_map, quality_cycles, validation_retries,
    crash_count, story_results, infra_issues,
    worktree_map, stage_timestamps, git_stats,
    pipeline_start_time, readiness_scores, team_name,
    business_answers, storage_mode, status_cache, skill_repo_path,
    project_brief, story_briefs, merge_status
  # Full state write enables Phase 0 recovery if lead crashes between heartbeats
```

## Structured Heartbeat Output

When no new worker messages received, output brief structured status and immediately let turn end.

**CRITICAL:** Lead must NEVER output "waiting", "standing by", or any passive phrase followed by turn end. This breaks the heartbeat loop — Stop hook will NOT fire if lead is passively waiting.

- **CORRECT:** Brief status → turn ends → Stop hook fires → next heartbeat
- **WRONG:** "Waiting for workers..." → turn ends → Stop hook does NOT fire → pipeline stalls

### Algorithm

```
ON NO NEW MESSAGES (heartbeat cycle with no worker updates):
  story_id = selected_story_id
  current_stage = extract_stage_number(story_state[story_id])

  # Determine current activity from checkpoint
  checkpoint = read(".pipeline/checkpoint-{story_id}.json") if exists
  IF checkpoint:
    activity = checkpoint.lastAction OR skill_name_from_stage(current_stage)
    progress_fraction = "{len(checkpoint.tasksCompleted)}/{len(checkpoint.tasksCompleted)+len(checkpoint.tasksRemaining)}"
  ELSE:
    activity = skill_name_from_stage(current_stage)
    progress_fraction = "—"

  # Increment heartbeat counter (ephemeral, resets on recovery)
  heartbeat_count++

  # Structured heartbeat output (single story)
  Output: """
Heartbeat #{heartbeat_count} — {story_id}
Stage {current_stage} | {activity} | Progress: {progress_fraction}
Next: {predict_next_step(current_stage)}
"""

  # FORBIDDEN outputs that break heartbeat:
  # "Waiting for workers to complete..."
  # "Standing by for worker updates..."
  # "No new messages. Continuing to monitor..."
  # "Awaiting completion..."
  #
  # Turn MUST end here immediately after brief status output.
  # Stop hook will fire → next heartbeat cycle begins.
```

## Helper Functions

### skill_name_from_stage(stage)

Maps stage number to skill name for activity display.

```
stage_to_skill = {
  0: "ln-300-task-coordinator",
  1: "ln-310-story-validator",
  2: "ln-400-story-executor",
  3: "ln-500-story-quality-gate"
}
RETURN stage_to_skill[stage]
```

### predict_next_step(current_stage)

Predicts next pipeline action based on current stage.

```
next_steps = {
  0: "Validation (ln-310) -> Todo",
  1: "Execution (ln-400) -> To Review",
  2: "Quality Gate (ln-500) -> Done/To Rework",
  3: "Sync with develop -> User confirmation -> Done"
}
RETURN next_steps[current_stage]
```

### extract_stage_number(state_string)

Extracts numeric stage from state enum.

```
# "STAGE_0" → 0, "STAGE_1" → 1, etc.
IF state_string matches "STAGE_(\d+)":
  RETURN int(matched_group_1)
ELSE:
  RETURN null
```

## Related Files

- **Message Handlers:** `phase4_handlers.md`
- **Git Flow:** `phase4a_git_merge.md`
- **Health Contract:** `worker_health_contract.md`
- **Checkpoint Format:** `checkpoint_format.md`

---
**Version:** 2.0.0
**Last Updated:** 2026-02-25
