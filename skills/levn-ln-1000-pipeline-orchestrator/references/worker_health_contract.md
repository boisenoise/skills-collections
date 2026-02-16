# Worker Health Contract

Worker lifecycle, health monitoring, and crash recovery for pipeline story workers.

## Worker Lifecycle

```
SPAWNED ──→ EXECUTING ──→ REPORTING ──→ SHUTDOWN
                │
                └──→ CRASHED (no completion message, idle without report)
```

Each worker handles exactly ONE stage. No IDLE→EXECUTING transition between stages.

| State | Description | Duration |
|-------|------------|----------|
| SPAWNED | Task() called, worker initializing | Seconds |
| EXECUTING | Worker running ln-300/310/400/500 via Skill tool | Minutes to hours (ln-400 can be long) |
| REPORTING | Worker sends "Stage N COMPLETE/ERROR" to lead | Seconds |
| SHUTDOWN | Lead sends shutdown_request after report, worker approves and exits | Seconds |
| CRASHED | Worker stopped without sending completion message | Detected by lead |

## Health Signal Matrix

| Signal | Meaning | Lead Action |
|--------|---------|-------------|
| Worker sends "Stage N COMPLETE" | Healthy, stage done | Shutdown worker, spawn fresh for next stage |
| Worker sends "Stage N ERROR" | Healthy, stage failed | Shutdown worker, decide retry/pause |
| TeammateIdle WITH done.flag existing | Normal: worker reported and awaiting shutdown | Send shutdown_request, remove flags |
| TeammateIdle WITHOUT done.flag AND no COMPLETE/ERROR | Suspicious: possible crash | Enter Crash Detection Protocol |
| No notification at all | Worker still executing | WAIT — do NOT interrupt. ln-400/ln-500 can run 30+ min |

**Critical rule:** TeammateIdle is NORMAL when `done.flag` exists — worker reported and is awaiting shutdown_request. Only suspicious when idle arrives without `done.flag` and no completion message.

## Crash Detection Protocol

3-step protocol. Goal: distinguish normal idle from actual crash with minimal false positives.

```
# Step 1: Flag suspicious
ON TeammateIdle for worker_map[id] WITHOUT "Stage N COMPLETE/ERROR":
  suspicious_idle[id] = true
  last_known_stage[id] = story_state[id]

# Step 2: Probe
SendMessage(recipient: worker_map[id],
            content: "Status check: are you still working on Stage {N} for {id}?",
            summary: "{id} health check")

# Step 3: Evaluate response
ON worker responds with parseable status:
  suspicious_idle[id] = false              # False alarm, worker alive
  # Continue normal operation

ON TeammateIdle again WITHOUT response:
  # Confirmed crash
  crash_count[id]++
  IF crash_count[id] <= 1:
    Respawn (see Respawn Rules below)
  ELSE:
    story_state[id] = "PAUSED"
    active_workers--
    ESCALATE: "Story {id} worker crashed twice at Stage {N}. Manual intervention required."
```

## Lost Message Recovery Protocol

Complements crash detection by actively verifying done-flags on each heartbeat. Handles edge case where worker writes `done.flag` after ACK but message delivery fails on subsequent heartbeat.

**Problem:** Worker writes `done.flag` after receiving ACK from lead (see `worker_prompts.md`). In rare cases, done.flag exists but worker's shutdown was not processed (e.g., lead crashed between ACK and shutdown). TeammateIdle hook returns `exit 0` (allows idle), so crash detection never triggers.

**Solution:** Proactive verification in heartbeat loop (SKILL.md Phase 4, Step 3).

```
ON HEARTBEAT (every ~60 seconds):
  FOR EACH active story (STAGE_0..STAGE_3):
    IF done.flag exists AND story_state NOT advanced:
      # Lost message detected: worker signaled completion but lead never processed it

      # Try 1: Synthetic recovery from checkpoint
      checkpoint = read(".pipeline/checkpoint-{id}.json")
      IF checkpoint.stage matches current stage:
        # Verify completion via kanban/Linear API
        Re-read kanban board
        IF work verified complete (tasks exist, status changed, etc.):
          SYNTHESIZE appropriate "Stage N COMPLETE" message
          Process through normal ON handler (Phase 4, Step 2)
        ELSE:
          SYNTHESIZE error message
          Process through error handler

      # Try 2: Fallback to probe protocol
      ELSE:
        # Checkpoint missing/invalid — cannot verify completion
        suspicious_idle[id] = true
        SendMessage(recipient: worker_name,
                   content: "Status check: are you still working on Stage {N} for {id}?",
                   summary: "{id} health check")
        # Wait for worker response or next TeammateIdle (handled by existing 3-step protocol)
```

**Trigger Conditions:**

| Condition | Meaning | Action |
|-----------|---------|--------|
| `done.flag` exists, state advanced | Normal: message received, handler processed | No action (cleanup happens in completion handler) |
| `done.flag` exists, state NOT advanced | Lost message: worker signaled but lead never received | Synthetic recovery OR probe |
| `done.flag` absent, no COMPLETE message | Crash or still working | Existing crash detection handles this (3-step protocol) |

**Recovery Verification (by stage):**

| Stage | Verification Method | Success Indicator | Failure Indicator |
|-------|---------------------|-------------------|-------------------|
| 0 | Re-read kanban board | Tasks exist under Story | Tasks missing despite done.flag |
| 1 | Re-read kanban board | Story status = Todo (GO) | Story still Backlog (NO-GO) |
| 2 | Re-read kanban board | Story status = To Review | Story not in To Review |
| 3 | Re-read kanban board + checkpoint.verdict | Story status = Done (PASS/CONCERNS/WAIVED) | Story status = To Rework (FAIL) |

**Advantages:**
- Detects lost messages within 1 heartbeat cycle (~60s) vs manual discovery
- Uses existing checkpoint infrastructure (no new state)
- Preserves reactive crash detection for genuine crashes (orthogonal mechanisms)
- No changes to worker protocol (backward compatible)
- Handles network issues, context overflow, worker crashes

**Defense-in-Depth:**
- **Reactive (3-step crash detection):** Handles crashes that prevent done.flag creation
- **Proactive (lost message recovery):** Handles lost messages after done.flag creation
- Together: comprehensive coverage of all failure modes

## Respawn Rules (Resume + Checkpoint)

When crash confirmed (Step 3). See `references/checkpoint_format.md` for checkpoint schema.

1. **Shutdown old worker** (best effort — may already be dead):
   ```
   SendMessage(type: "shutdown_request", recipient: worker_map[id])
   ```

2. **Decrement counter:**
   ```
   active_workers--
   ```

3. **Try resume with agentId** (preserves full conversation context):
   ```
   checkpoint = read(".pipeline/checkpoint-{id}.json")
   IF checkpoint.agentId exists:
     Task(resume: checkpoint.agentId)
     # If resume succeeds → worker continues exactly where it left off
   ```

4. **Fallback: new worker with checkpoint context** (if resume fails or no checkpoint):
   ```
   new_worker = "story-{id}-s{checkpoint.stage}-retry"
   new_prompt = worker_prompt(story, checkpoint.stage, business_answers, worktree_map[id], project_root) + """
     CHECKPOINT RESUME — DO NOT re-execute completed work.
     Tasks already completed: {checkpoint.tasksCompleted}
     Tasks remaining: {checkpoint.tasksRemaining}
     Last action: {checkpoint.lastAction}
     Continue from remaining tasks only.
   """
   Task(name: new_worker, team_name: "pipeline-{date}",
        model: "opus", mode: "bypassPermissions",              # Opus high effort for crash recovery
        subagent_type: "general-purpose", prompt: new_prompt)
   worker_map[id] = new_worker
   active_workers++
   ```

## Respawn Limits

| Counter | Initial | Limit | On Limit |
|---------|---------|-------|----------|
| `crash_count[id]` | 0 | 1 | 2nd crash → PAUSED + escalate |

**Rationale:** Single respawn handles transient failures (context overflow, network glitch). Double crash = systematic issue requiring human input.

## Zombie Workers (Expected Behavior)

When a worker crashes and is respawned (crash recovery protocol), the old crashed worker may remain in the team as a "zombie" — an agent that doesn't respond to shutdown requests but stays in the team roster.

**Why zombies occur:**
1. Lead sends `shutdown_request` to crashed worker (best-effort cleanup)
2. Crashed worker cannot respond (already dead/hung)
3. Lead proceeds with respawn (cannot wait indefinitely)
4. Old worker remains in `~/.claude/teams/pipeline-{date}/members`

**Impact (minimal):**
- Old worker listed in team roster but inactive
- May receive broadcast messages (wasted delivery, but broadcasts are rare)
- Does NOT consume active context (crashed workers don't process turns)
- Does NOT block progress (lead continues with new worker)

**Cleanup strategy:**
- **During pipeline:** Zombies persist (acceptable tradeoff for responsiveness)
- **At Phase 5 (Final Cleanup):** `TeamDelete` removes entire team including all zombies
- **Manual cleanup (if needed):** User can inspect `~/.claude/teams/pipeline-{date}/` and remove zombie agents

**Why not force-remove during pipeline:**
- Adds complexity to mid-pipeline coordination
- Risk of removing wrong worker (race conditions with team membership)
- Zombies have minimal impact on ongoing work
- Batch cleanup at Phase 5 is simpler and safer

**Design decision:** Accept temporary zombies during pipeline execution, clean all at Phase 5. Prioritizes pipeline robustness and simplicity over perfect team hygiene.

## Graceful Shutdown Protocol

Lead-initiated shutdown sequence:

```
# 1. Lead sends request
SendMessage(type: "shutdown_request", recipient: worker_map[id],
            content: "Pipeline complete for {id}. Shutting down.")

# 2. Worker responds
#    - approve: true  → worker exits cleanly
#    - approve: false → worker still working, lead waits

# 3. If worker doesn't respond (already crashed)
#    → No action needed, worker already gone
#    → Lead proceeds to next story or cleanup
```

**Rule:** Always attempt graceful shutdown before cleanup. Never force-kill via TaskStop.

## Keepalive Hooks

Two hooks prevent premature termination. Installed by lead in Phase 3 from `references/hooks/`.

| Hook | File | Trigger | Exit 2 Condition |
|------|------|---------|-----------------|
| Stop | `pipeline-keepalive.sh` | Claude tries to stop | `complete: false` AND `session_id` matches `.pipeline/lead-session.id` |
| TeammateIdle | `worker-keepalive.sh` | Worker goes idle | `active.flag`* exists AND `done.flag`* does NOT exist |

*Short names. Full paths: `.pipeline/worker-{name}-active.flag`, `.pipeline/worker-{name}-done.flag`

**Flag lifecycle:**
```
SPAWNED   → lead creates .pipeline/worker-{name}-active.flag
EXECUTING → active.flag exists, done.flag absent → TeammateIdle returns exit 2
REPORTING → worker sends "Stage N COMPLETE/ERROR" via SendMessage
            → TeammateIdle returns exit 2 (still working, no done.flag yet)
ACK       → lead sends "ACK Stage N for {id}" → worker writes .pipeline/worker-{name}-done.flag
            → TeammateIdle returns exit 0 → worker goes idle (can receive shutdown_request)
PROCESSED → lead sends ACK, removes both flags, processes message (state transitions, spawn next worker)
SHUTDOWN  → lead sends shutdown_request → worker approves and exits
```

**Lead responsibilities:**
- Write `.pipeline/state.json` with `complete: false` at pipeline start (Phase 3)
- Write `.pipeline/lead-session.id` with current session_id (Phase 3) — Stop hook only keeps lead alive
- Create `.pipeline/worker-{name}-active.flag` when assigning stage
- Remove both `active.flag` and `done.flag` AT START of completion message handler (before state transitions)
- Set `complete: true` in Phase 5 before cleanup

## Lead Heartbeat Loop

The Stop hook drives the lead's event loop. The lead does **NOT** passively wait — it actively processes messages on each heartbeat cycle.

```
Lead turn ends → Stop event → pipeline-keepalive.sh → exit 2
  → stderr "HEARTBEAT: N workers, M stories..."
  → New agentic loop iteration (NOT a user turn)
  → Queued worker messages (SendMessage) delivered in this cycle
  → Lead processes via ON handlers in Phase 4
  → Turn ends → next heartbeat
```

**Key points:**
- Stop hook exit 2 = heartbeat trigger, NOT just "prevent exit"
- Each heartbeat creates a new processing cycle where worker messages arrive
- Lead MUST NOT output "waiting for messages" and stop — the heartbeat keeps it running
- If no worker messages: output brief status (`"Heartbeat: N workers active"`), let turn end
- Frequency: ~60 seconds per cycle (throttled by `sleep 60` in Stop hook)
- Stage transitions = shutdown old worker + spawn fresh (net-zero active_workers)

**Anti-pattern:** Lead says "I'm waiting for workers" and sits idle. This breaks the pipeline because the lead's turn has ended and it cannot process future messages.

**Correct pattern:** Lead processes all available messages, outputs brief status, lets turn end naturally. Stop hook fires, next heartbeat cycle begins.

## Lead Recovery Protocol

When ln-1000 restarts on clean context (crash, context overflow, user interrupt), it must recover all state from `.pipeline/state.json`. See SKILL.md Phase 0.

### State Persistence

Lead writes ALL state variables to `.pipeline/state.json` on **every heartbeat cycle** (not just `last_check`). This ensures recovery loses at most one heartbeat cycle of state.

| Variable | Persisted in state.json | Recovery Notes |
|----------|------------------------|----------------|
| `complete` | Yes | Core pipeline flag |
| `active_workers` | Yes | May be stale if workers crashed during lead downtime |
| `stories_remaining` | Yes | Recalculate from story_state on recovery |
| `last_check` | Yes | Timestamp of last heartbeat |
| `story_state` | Yes | Per-story stage mapping |
| `worker_map` | Yes | Worker names — validate against team config |
| `quality_cycles` | Yes | FAIL→retry counters |
| `validation_retries` | Yes | NO-GO retry counters |
| `crash_count` | Yes | Respawn counters |
| `priority_queue_ids` | Yes | Remaining queue order |
| `worktree_map` | Yes | Story → worktree directory mapping |
| `depends_on` | Yes | Story → prerequisite IDs mapping |
| `story_results` | Yes | Per-story stage results for report |
| `infra_issues` | Yes | Infrastructure problems list |
| `stage_timestamps` | Yes | Per-stage start/end times for duration tracking |
| `git_stats` | Yes | Lines added/deleted/files changed per story |
| `pipeline_start_time` | Yes | Pipeline start for wall-clock duration |
| `readiness_scores` | Yes | From Stage 1 GO, for Stage 3 fast-track |
| `team_name` | Yes | Team name for Task() spawns |
| `business_answers` | Yes | Phase 2 answers passed to worker prompts |
| `storage_mode` | Yes | "file" or "linear" task backend |
| `status_cache` | Yes | Linear status name→UUID mapping |
| `skill_repo_path` | Yes | Skills repository path for recovery |
| `project_brief` | Yes | Project context (name, tech, type, key_rules) from CLAUDE.md |
| `story_briefs` | Yes | Per-story orchestrator briefs from Linear ORCHESTRATOR_BRIEF markers |
| `suspicious_idle` | No (ephemeral) | Reset to false on recovery |

### Recovery Sequence

```
1. Read .pipeline/state.json → restore all persisted variables
2. Read .pipeline/checkpoint-*.json → validate story_state matches checkpoints
3. Re-read kanban board → verify consistency with story_state
4. Read team config → verify worker_map members still exist
5. For each active story (STAGE_0..STAGE_3):
   a. Try Task(resume: checkpoint.agentId) — preserves full context
   b. Fallback: respawn with checkpoint context (see Respawn Rules)
6. Resume Phase 4 event loop
```

### What Recovery Cannot Restore

- **In-flight messages:** Messages sent by workers during lead downtime are lost. Workers will re-idle, triggering crash detection on next heartbeat.
- **Partial kanban updates:** If lead crashed mid-write, kanban may be inconsistent. Recovery re-reads and trusts pipeline state over kanban.

## Forbidden Patterns

Workers and lead MUST NOT use any of these patterns:

| Pattern | Why Forbidden | Correct Alternative |
|---------|-------------|-------------------|
| Read `~/.claude/teams/*/inboxes/*.json` | Internal format, undocumented, fragile | Messages arrive automatically as conversation turns |
| `sleep N` + poll loop | Blocks agent, can't receive messages while sleeping | WAIT (idle) — Claude Code delivers messages |
| Parse `permission_request` JSON | Internal protocol, changes without notice | Use `mode: "bypassPermissions"` at spawn |
| Parse `idle_notification` JSON | Internal protocol | Use TeammateIdle hook or ON handlers |
| `Bash(cat ~/.claude/...)` | Internal file structure | Use SendMessage for all communication |
| Process message without sender check | Stale messages from old workers cause incorrect state transitions | Verify `message.sender == worker_map[id]` before any ON handler |

---
**Version:** 1.0.0
**Last Updated:** 2026-02-13
