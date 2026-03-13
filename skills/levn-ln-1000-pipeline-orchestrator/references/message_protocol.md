# Message Protocol

Formal contract for SendMessage communication between pipeline lead and story workers.

## Worker -> Lead: Completion Reports

Workers MUST use exact formats below. Lead parses messages by regex — deviations are unparseable and trigger escalation.

### Success Messages

| Stage | Name | Format |
|-------|------|--------|
| 0 | Task Planning | `Stage 0 COMPLETE for {id}. {N} tasks created. Plan score: {score}/4.` |
| 1 | Validation | `Stage 1 COMPLETE for {id}. Verdict: GO. Readiness: {score}. Agents: {agents_info}.` |
| 2 | Implementation | `Stage 2 COMPLETE for {id}. All tasks Done. Story set to To Review.` |
| 3 | Quality Gate | `Stage 3 COMPLETE for {id}. Verdict: {PASS\|CONCERNS\|WAIVED}. Quality Score: {score}/100. Agents: {agents_info}.` |

### Error/Failure Messages

| Stage | Name | Format |
|-------|------|--------|
| 0 | Task Planning | `Stage 0 ERROR for {id}: {details}` |
| 1 | Validation | `Stage 1 COMPLETE for {id}. Verdict: NO-GO. Readiness: {score}. Reason: {reason}. Agents: {agents_info}.` |
| 2 | Implementation | `Stage 2 ERROR for {id}: {details}` |
| 3 | Quality Gate | `Stage 3 COMPLETE for {id}. Verdict: FAIL. Quality Score: {score}/100. Issues: {list}. Agents: {agents_info}.` |

### Agents Info Format

The `{agents_info}` field reports agent review results. Required for Stage 1 and Stage 3 messages.

| Value | Meaning |
|-------|---------|
| `codex(2/3),gemini(1/2)` | Both agents used; accepted/total suggestions |
| `codex(1/2),gemini(FAILED)` | One agent failed |
| `SKIPPED(no agents available)` | Health check returned 0 agents |
| `SKIPPED(agents disabled)` | All agents disabled in environment_state.json |
| `SKIPPED(fast-track)` | Stage 3 fast-track mode skipped agent review |
| `SKIPPED(pipeline-efficiency)` | Stage 3 skipped for pipeline speed; regression tests + lint still run |

**Backward compatibility:** If `Agents:` field is absent in a message, lead stores `"N/A"` (supports workers from older prompts).

### Diagnostic Response

When lead sends `"Status check"`, worker responds:

```
Status for {id}: Stage {N} {EXECUTING|WAITING|ERROR}. Current step: {description}.
```

## Lead -> Worker: Commands

Each worker receives exactly ONE `Execute Stage` command per lifetime. Stage transitions spawn new workers (fresh context per stage).

| Command | Format | When |
|---------|--------|------|
| Start stage | `Execute Stage {N} for {id}` | Initial assignment after spawn (one per worker) |
| Diagnostic | `Status check: are you still working on Stage {N} for {id}?` | Crash detection probe |
| Shutdown | `SendMessage(type: "shutdown_request", recipient: "story-{id}-{stage_name}")` | After stage completion or PAUSED |
| ACK | `ACK Stage {N} for {id}` | After processing completion message (confirms receipt) |

## Lead Parsing Regex

Lead extracts structured data from worker messages:

```
# Stage completion — COMPLETE uses "." separator, ERROR uses ":" separator
^Stage (\d) COMPLETE for ([A-Z]+-\d+)\.\s*(.*)$
^Stage (\d) ERROR for ([A-Z]+-\d+):\s*(.*)$
# NOTE: Story ID pattern [A-Z]+-\d+ requires uppercase prefix (e.g., PROJ-42). Non-standard formats will fail parsing.

# COMPLETE regex groups: 1=stage, 2=story ID, 3=details (parsed further per stage)
# ERROR regex groups:   1=stage, 2=story ID, 3=error details

# Stage 0 details
(\d+) tasks created\. Plan score: (\d)/4

# Stage 1 details
Verdict: (GO|NO-GO)\. Readiness: (\d+).*?(?:Agents: (.+?)\.)?$

# Stage 3 details
Verdict: (PASS|CONCERNS|WAIVED|FAIL)\. Quality Score: (\d+)/100.*?(?:Agents: (.+?)\.)?$

# Agents info (optional, captured from Stage 1 and Stage 3)
# Group captures: SKIPPED(reason) | codex(N/M),gemini(N/M) | codex(N/M),gemini(FAILED)
# If group is empty/absent → store as "N/A"
```

## SendMessage Contract

### Worker -> Lead

```
SendMessage(
  type: "message",
  recipient: "team-lead",
  content: <exact format from tables above>,
  summary: "{id} Stage {N} {verdict/result}"    # max 10 words
)
```

### Lead -> Worker

```
# Command / Diagnostic / Shutdown:
SendMessage(
  type: "message",
  recipient: "story-{id}-{stage_name}",  # decompose | validate | implement | qa
  content: <exact format from Commands table>,
  summary: "{id} -> Stage {N}"                  # max 10 words
)

# ACK:
SendMessage(
  recipient: worker_map[id],
  content: "ACK Stage {N} for {id}",
  summary: "{id} Stage {N} ACK"                 # max 10 words
)
```

## Unparseable Message Handling

If lead cannot parse worker message (doesn't match regex):
1. Log raw message content
2. Send diagnostic: `"Status check: are you still working on Stage {N} for {id}?"`
3. If worker responds with parseable status → continue
4. If still unparseable → `story_state[id] = "PAUSED"`, escalate to user

## ACK Protocol

Lead acknowledges every successfully processed completion message. Workers wait for ACK before writing done.flag.

### ACK Flow

```
Worker -> Lead: "Stage N COMPLETE for {id}..."     # completion report
Lead processes ON handler (state transition, spawn next worker)
Lead -> Worker: "ACK Stage {N} for {id}"           # confirmation
Lead -> Worker: shutdown_request                    # lifecycle end
Worker: writes done.flag, approves shutdown
```

### ACK Format

| Direction | Format | When |
|-----------|--------|------|
| Lead -> Worker | `ACK Stage {N} for {id}` | After ON handler completes successfully |
| Lead -> Worker (dup) | `ACK Stage {N} for {id}` | State guard detects duplicate — re-send ACK, skip processing |

### Lost Message Recovery (with ACK)

```
1. Worker sends report → message lost
2. No ACK arrives → no done.flag written
3. Worker stays alive (keepalive hook: no done.flag → exit 2)
4. Lead heartbeat: probes worker → worker responds with status
5. Worker retries report → lead processes → sends ACK
6. Worker writes done.flag → approves shutdown
```

**Improvement over pre-ACK:** Lost messages detected immediately (no done.flag → worker alive) instead of waiting for heartbeat verification (~60s). Worker retries proactively.

### Retry Limits

Worker retries report up to 1 time after probe. If still no ACK after retry → approve shutdown regardless (heartbeat verification is final safety net).

---
**Version:** 2.0.0
**Last Updated:** 2026-03-09
