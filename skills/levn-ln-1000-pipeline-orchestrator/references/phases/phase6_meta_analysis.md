# Phase 6: Meta-Analysis Implementation

Pipeline-specific implementation of `shared/references/meta_analysis_protocol.md` (execution-orchestrator type).

Runs after Phase 5 completes. Appends `## Meta-Analysis` section to the pipeline report and updates the cross-run quality trend tracker.

## 1. Worker & Skill Effectiveness Audit

```
skill_map = {0: "ln-300", 1: "ln-310", 2: "ln-400", 3: "ln-500"}

FOR stage IN 0..3:
  worker_status = "✓ OK"
  IF crash_count for this stage > 0: worker_status = "⚠ Crashed (recovered)"
  IF infra_issues has entry for this stage: worker_status = "⚠ Infra issue"
  IF stage not completed (no timestamp): worker_status = "✗ Not reached"

  skill_status = "✓" IF:
    stage 0 → plan_score >= 3
    stage 1 → verdict == "GO"
    stage 2 → story_state[id] != "PAUSED"
    stage 3 → verdict IN ("PASS", "CONCERNS", "WAIVED")
  ELSE "⚠" (degraded) or "✗" (failed/not reached)

  skill_result = {
    0: "Plan {score}/4, {N} tasks",
    1: "{GO/NO-GO}, Readiness {score}/10",
    2: "{files} files, +{add}/-{del}",
    3: "{verdict}, Score {score}/100, {rework} rework"
  }[stage]
```

## 2. Problems & Recovery Actions

```
recovery_map = {
  "message_delivery": "Fix recipient: 'team-lead' in worker_prompts.md",
  "crash":            "Review checkpoint coverage in phase4_heartbeat.md",
  "ack_timeout":      "Check keepalive hook installation (Phase 3.1 settings_template)"
}
```

## 3. Improvement Candidates (Focus Areas)

Per protocol §4: tied to specific weaknesses of THIS run, not generic.

```
candidates = []
IF any infra_issue.type == "message_delivery":
  candidates += "message_delivery failure → Fix recipient name in worker_prompts.md"
IF quality_cycles[id] > 1:
  candidates += "{quality_cycles} rework cycles → improve test spec coverage in ln-520"
IF crash_count[id] > 0:
  candidates += "{crash_count} crash(es) → verify checkpoint coverage in phase4_heartbeat.md"
IF stage_durations.get(2, 0) > 10800:  # 3h
  candidates += "Stage 2 > 3h → consider task decomposition for complex stories"
```

## 4. Trend Tracking

Read + append to `docs/tasks/reports/quality-trend.md` (create with header if missing):

```
Header: | Date | Story | Score | Rework | Crashes | Infra Issues |
Row:    | {date} | {story_id} | {score}/100 | {quality_cycles} | {crash_count} | {len(infra_issues)} |
```

Per protocol §4: IF previous row exists, note trend direction (improving/stable/declining).

## 5. Assumption Audit

Per protocol §5: compare actual outcome vs pre-execution expectations.
- Did the pipeline stages deliver what planning predicted?
- What surprised (unexpected rework, crashes, infra issues)?
- What would be done differently next time?

## 6. Report Output

Append to `docs/tasks/reports/pipeline-{date}.md`:

```
---

## Meta-Analysis

### Worker & Skill Effectiveness

| Stage | Skill  | Duration | Worker   | Skill Result                             |
|-------|--------|----------|----------|------------------------------------------|
| 0     | ln-300 | {dur}    | {✓/⚠/✗} | Plan {score}/4, {N} tasks                |
| 1     | ln-310 | {dur}    | {✓/⚠/✗} | {GO/NO-GO}, Readiness {score}/10         |
| 2     | ln-400 | {dur}    | {✓/⚠/✗} | {files} files, +{add}/-{del}             |
| 3     | ln-500 | {dur}    | {✓/⚠/✗} | {verdict}, Score {score}/100, {rework} rework |

### Problems & Limitations

{IF infra_issues empty: "None detected."}
{ELSE:
| # | Stage   | Type             | Description          | Recovery Action                          |
|---|---------|------------------|----------------------|------------------------------------------|
{row per infra_issue}
}

### Improvement Candidates

{IF candidates: numbered list of focus areas}
{ELSE: "None — pipeline ran clean."}

### Assumptions

{what matched vs what surprised — per protocol §5}
```
