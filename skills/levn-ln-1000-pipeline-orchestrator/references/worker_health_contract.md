# Worker Health Contract

Worker lifecycle, health monitoring, and crash recovery for pipeline story workers.

## Worker Lifecycle

```
SPAWNED ──→ EXECUTING ──→ REPORTING ──→ SHUTDOWN
                │
                └──→ CRASHED (no completion message, idle without report)
```

Each worker handles exactly ONE stage (or one plan). No IDLE→EXECUTING transition between stages.

### Plan Workers (Plan Gate)

A read-only plan worker runs before the execute worker for each stage:

```
SPAWNED ──→ ANALYZING ──→ PLAN_RESULT ──→ [APPROVE] ──→ SHUTDOWN
                                │
                                └──→ [REVISE] ──→ ANALYZING (max 2 revisions)
                                │
                                └──→ [LIMIT] ──→ Lead PAUSES + ESCALATES
```

Plan workers follow the same health contract as execute workers (crash detection, keepalive hooks, done.flag), with differences:
- **Read-only:** DO NOT invoke Skill(), modify files, or update Linear/kanban
- **Communication:** Send `PLAN_RESULT` instead of `Stage N COMPLETE/ERROR`
- **Shutdown trigger:** `PLAN_APPROVE` from Lead (not ACK after completion)
- **Naming:** `story-{id}-s{N}-plan` (suffix `-plan`)

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

3-step protocol (flag → probe → respawn). Full implementation: `phases/phase4_handlers.md` → Crash Detection Handler.

**Summary:** (1) Flag suspicious on idle without report. (2) Probe with status check message. (3) If no response on next idle → confirmed crash → respawn or escalate.

## Lost Message Recovery

Proactive done-flag verification on each heartbeat. Full algorithm: `phases/phase4_heartbeat.md` → Active Done-Flag Verification.

**Summary:** If `done.flag` exists but state not advanced → lost message. Recover from checkpoint + kanban verification, or fallback to probe protocol.

**Defense-in-Depth:**
- **Reactive (3-step crash detection):** Handles crashes that prevent done.flag creation
- **Proactive (lost message recovery):** Handles lost messages after done.flag creation

## Respawn Rules (Resume + Checkpoint)

When crash confirmed (Step 3). See `references/checkpoint_format.md` for checkpoint schema.

1. **Shutdown old worker** (best effort — may already be dead):
   ```
   SendMessage(type: "shutdown_request", recipient: worker_map[id])
   ```

2. **Try resume with agentId** (preserves full conversation context):
   ```
   checkpoint = read(".pipeline/checkpoint-{id}.json")
   IF checkpoint.agentId exists:
     Task(resume: checkpoint.agentId)
     # If resume succeeds → worker continues exactly where it left off
   ```

3. **Fallback: new worker with checkpoint context** (if resume fails or no checkpoint):
   ```
   new_worker = "story-{id}-s{checkpoint.stage}-retry"
   new_prompt = worker_prompt(story, checkpoint.stage, business_answers) + """
     CHECKPOINT RESUME — DO NOT re-execute completed work.
     Tasks already completed: {checkpoint.tasksCompleted}
     Tasks remaining: {checkpoint.tasksRemaining}
     Last action: {checkpoint.lastAction}
     Continue from remaining tasks only.
   """
   Task(name: new_worker, team_name: "pipeline-{date}",
        model: "opus", mode: "bypassPermissions",
        subagent_type: "general-purpose", prompt: new_prompt)
   worker_map[id] = new_worker
   ```

## Respawn Limits

| Counter | Initial | Limit | On Limit |
|---------|---------|-------|----------|
| `crash_count[id]` | 0 | 1 | 2nd crash → PAUSED + escalate |

**Rationale:** Single respawn handles transient failures (context overflow, network glitch). Double crash = systematic issue requiring human input.

## Zombie Workers

Crashed workers may remain in team roster as inactive zombies. Minimal impact — they don't consume context or block progress. Cleaned up by `TeamDelete` in Phase 5 (or force-cleaned if TeamDelete blocked by hung agent).

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
#    → Lead proceeds to cleanup
```

**Rule:** Always attempt graceful shutdown before cleanup. If TeamDelete blocked by hung agent (#31788), force-clean team resources (see SKILL.md Phase 5 step 6).

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
PROCESSED → lead removes active.flag and done.flag at handler start (defensive cleanup before state transition)
SHUTDOWN  → lead sends shutdown_request → worker approves and exits
```

**Note on flag lifecycle:** Lead removes both `active.flag` and `done.flag` at the START of each completion handler (defensive cleanup). If the handler spawns a new worker, that worker gets fresh flags. The old `done.flag` does NOT persist between stages — it is cleaned up by the handler, not Phase 5.

**Lead responsibilities:**
- Write `.pipeline/state.json` with `complete: false` at pipeline start (Phase 3)
- Write `.pipeline/lead-session.id` with current session_id (Phase 3) — Stop hook only keeps lead alive
- Create `.pipeline/worker-{name}-active.flag` when assigning stage
- Remove both `active.flag` and `done.flag` AT START of completion message handler (defensive cleanup before state transitions)
- Set `complete: true` in Phase 5 before cleanup

## Lead Heartbeat Loop

The Stop hook drives the lead's event loop via exit code 2 → new agentic loop. Full details: `AGENT_TEAMS_PLATFORM_GUIDE.md` §2, `phases/phase4_heartbeat.md`.

**Key rule:** Lead MUST NOT output "waiting for messages" — this breaks the heartbeat loop. Output brief status, let turn end naturally.

## Lead Recovery Protocol

When ln-1000 restarts on clean context (crash, context overflow, user interrupt), it must recover all state from `.pipeline/state.json`. See SKILL.md Phase 0.

### State Persistence

Lead writes ALL state variables to `.pipeline/state.json` on **every heartbeat cycle**. Recovery loses at most one heartbeat cycle.

**Schema:** See `checkpoint_format.md` → Pipeline State Schema.

Ephemeral variables (NOT persisted, reset on recovery):

| Variable | Reset Value | Notes |
|----------|-------------|-------|
| `suspicious_idle` | `false` | Crash detection flag |
| `heartbeat_count` | `0` | Display counter only |

### Recovery Sequence

```
1. Read .pipeline/state.json → restore all persisted variables
2. Read .pipeline/checkpoint-*.json → validate story_state matches checkpoints
3. Re-read kanban board → verify consistency with story_state
4. Read team config → verify worker_map members still exist
5. For active story (selected_story_id):
   a. Try Task(resume: checkpoint.agentId) — preserves full context
   b. Fallback: respawn with checkpoint context (see Respawn Rules)
6. Resume Phase 4 event loop
```

### What Recovery Cannot Restore

- **In-flight messages:** Messages sent by workers during lead downtime are lost. Workers will re-idle, triggering crash detection on next heartbeat.
- **Partial kanban updates:** If lead crashed mid-write, kanban may be inconsistent. Recovery re-reads and trusts pipeline state over kanban.

---
**Version:** 3.0.0
**Last Updated:** 2026-03-09
