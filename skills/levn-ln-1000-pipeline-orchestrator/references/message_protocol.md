# Message Protocol

Formal contract for SendMessage communication between pipeline lead and story workers.

## Worker -> Lead: Completion Reports

Workers MUST use exact formats below. Lead parses messages by regex — deviations are unparseable and trigger escalation.

### Success Messages

| Stage | Format |
|-------|--------|
| 0 | `Stage 0 COMPLETE for {id}. {N} tasks created. Plan score: {score}/4.` |
| 1 | `Stage 1 COMPLETE for {id}. Verdict: GO. Readiness: {score}.` |
| 2 | `Stage 2 COMPLETE for {id}. All tasks Done. Story set to To Review.` |
| 3 | `Stage 3 COMPLETE for {id}. Verdict: {PASS\|CONCERNS\|WAIVED}. Quality Score: {score}/100.` |

### Error/Failure Messages

| Stage | Format |
|-------|--------|
| 0 | `Stage 0 ERROR for {id}: {details}` |
| 1 | `Stage 1 COMPLETE for {id}. Verdict: NO-GO. Readiness: {score}. Reason: {reason}` |
| 2 | `Stage 2 ERROR for {id}: {details}` |
| 3 | `Stage 3 COMPLETE for {id}. Verdict: FAIL. Quality Score: {score}/100. Issues: {list}` |

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
| Shutdown | `SendMessage(type: "shutdown_request", recipient: "story-{id}-s{N}")` | After stage completion or PAUSED |

## Lead Parsing Regex

Lead extracts structured data from worker messages:

```
# Stage completion (all stages)
^Stage (\d) (COMPLETE|ERROR) for ([A-Z]+-\d+)\.\s*(.*)$

# Group 1: stage number
# Group 2: COMPLETE or ERROR
# Group 3: story ID
# Group 4: details (parsed further per stage)

# Stage 0 details
(\d+) tasks created\. Plan score: (\d)/4

# Stage 1 details
Verdict: (GO|NO-GO)\. Readiness: (\d+)

# Stage 3 details
Verdict: (PASS|CONCERNS|WAIVED|FAIL)\. Quality Score: (\d+)/100
```

## SendMessage Contract

### Worker -> Lead

```
SendMessage(
  type: "message",
  recipient: "pipeline-lead",
  content: <exact format from tables above>,
  summary: "{id} Stage {N} {verdict/result}"    # max 10 words
)
```

### Lead -> Worker

```
SendMessage(
  type: "message",
  recipient: "story-{id}-s{N}",
  content: <exact format from Commands table>,
  summary: "{id} -> Stage {N}"                  # max 10 words
)
```

## Unparseable Message Handling

If lead cannot parse worker message (doesn't match regex):
1. Log raw message content
2. Send diagnostic: `"Status check: are you still working on Stage {N} for {id}?"`
3. If worker responds with parseable status → continue
4. If still unparseable → `story_state[id] = "PAUSED"`, escalate to user

---
**Version:** 1.0.0
**Last Updated:** 2026-02-13
