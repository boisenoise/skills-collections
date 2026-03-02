# Phase 4a: Git Sync, Report & Merge Confirmation

Git operations after Stage 3 PASS. Sync with develop, collect metrics, generate report, then ask user for merge confirmation. Merge only on explicit approval.

## Git Context

All git commands use `git -C {worktree_map[id]}`. The worker operates in its own worktree with a named feature branch (`feature/{id}-{slug}`).

---

## Section A: Sync & Report (automatic after Stage 3 PASS)

### Step 1: Sync with Develop

Pull latest changes from origin/develop into feature branch.

```
dir = worktree_map[id]

git -C {dir} fetch origin develop
git -C {dir} rebase origin/develop

IF rebase conflict:
  git -C {dir} rebase --abort
  git -C {dir} merge origin/develop    # Fallback to merge

  IF merge conflict:
    ESCALATE to user: "Merge conflict in Story {id}. Manual resolution required."
    story_state[id] = "PAUSED"
    # Do NOT remove worktree — user needs it to resolve conflicts
    RETURN
```

**Conflict Handling:**
- Try rebase first (clean linear history)
- Fallback to merge if rebase fails
- On merge conflict: PAUSED, escalate to user, preserve worktree for resolution

### Step 2: Collect Code Metrics

Capture diff statistics for pipeline report.

```
diff_output = git -C {dir} diff --stat develop...HEAD
git_stats[id] = parse_diff_stat(diff_output)
# Result: {lines_added: N, lines_deleted: N, files_changed: N}
# parse_diff_stat extracts numbers from git's "N files changed, N insertions(+), N deletions(-)" summary line
```

### Step 3: Append Story Report

Document Story completion in pipeline report.

```
Append to docs/tasks/reports/pipeline-{date}.md:
  ### {storyId}: {storyTitle} — {verdict}
  | Stage | Result | Duration | Details |
  |-------|--------|----------|---------|
  | 0 | {story_results[id].stage0 or "skip"} | {stage_duration(id, 0) or "—"} | |
  | 1 | {story_results[id].stage1 or "skip"} | {stage_duration(id, 1) or "—"} | retries: {validation_retries[id]} |
  | 2 | {story_results[id].stage2 or "skip"} | {stage_duration(id, 2) or "—"} | rework cycles: {quality_cycles[id]} |
  | 3 | {story_results[id].stage3 or "skip"} | {stage_duration(id, 3) or "—"} | crashes: {crash_count[id]} |
  **Branch:** feature/{id}-{slug}
  **Code:** +{git_stats[id].lines_added} / -{git_stats[id].lines_deleted} ({git_stats[id].files_changed} files)
  **Problems:** {list from counters, or "None"}
```

### Step 4: Verify Kanban + Linear Sync

```
# Verify kanban
Re-read kanban board

# Verify Linear sync (if applicable)
IF storage_mode == "linear":
  Read Linear issue via MCP
  IF status mismatch: LOG warning but do NOT block
```

---

## Section B: User Confirmation

Present merge summary and ask for explicit confirmation.

```
Output:
  Story {id} completed. Quality Score: {score}/100. Verdict: {verdict}.
  Branch: feature/{id}-{slug}
  Files changed: {git_stats[id].files_changed}
  Code: +{git_stats[id].lines_added} / -{git_stats[id].lines_deleted}

  Report: docs/tasks/reports/pipeline-{date}.md

AskUserQuestion: "Merge feature/{id}-{slug} to develop?"
```

Based on user response, proceed to Section C (merge) or Section D (decline).

---

## Section C: Merge (user confirmed)

### Step 1: Squash Merge into Develop

Merge from main directory (where develop is already checked out). Git forbids checking out the same branch in multiple worktrees, so `git -C {worktree} checkout develop` would fail.

```
# Main directory already has develop checked out (Phase 3.3)
git merge --squash feature/{id}-{slug}
git commit -m "{storyId}: {Story Title}"
git push origin develop
```

**Squash Commit Message Format:**
```
{storyId}: {Story Title}
```

### Step 2: Cleanup Worktree

```
git worktree remove .worktrees/story-{id} --force
worktree_map[id] = null
# Feature branch feature/{id}-{slug} is NOT deleted — preserved for git history
```

### Step 3: Context Refresh

**MANDATORY READ:** Reload main SKILL.md to refresh pipeline context after develop push.

### Step 4: Update State

```
story_state[id] = "DONE"
merge_status = "merged"
Update kanban: Story -> Done
Update .pipeline/state.json
```

---

## Section D: Decline (user declined merge)

### Step 1: Preserve Branch

Worktree is NOT removed — user may need it for manual merge later.

```
merge_status = "declined"
story_state[id] = "DONE"
Update kanban: Story -> Done    # Work IS complete, merge is deployment decision
Update .pipeline/state.json
```

### Step 2: Log in Report

```
Append to docs/tasks/reports/pipeline-{date}.md:
  **Merge:** Declined by user. Branch feature/{id}-{slug} preserved.
```

### Step 3: Output Manual Merge Instructions

```
Output:
  Branch feature/{id}-{slug} preserved. To merge manually:
  git checkout develop
  git merge --squash feature/{id}-{slug}
  git commit -m "{storyId}: {Story Title}"
  git push origin develop
```

---

## Error Recovery

| Error | Severity | Action |
|-------|----------|--------|
| Rebase conflict | Medium | Fallback to merge |
| Merge conflict (sync) | High | PAUSED, escalate, preserve worktree for resolution |
| Push failure | High | PAUSED, escalate (network/permissions issue) |
| Kanban/Linear mismatch | Low | LOG warning, continue |

## Related Files

- **Message Handlers:** `phase4_handlers.md` (calls Section A after Stage 3 PASS)
- **Heartbeat:** `phase4_heartbeat.md`
- **Pipeline States:** `pipeline_states.md` (PENDING_MERGE state)
- **Checkpoint Format:** `checkpoint_format.md`

---
**Version:** 2.0.0
**Last Updated:** 2026-02-25
