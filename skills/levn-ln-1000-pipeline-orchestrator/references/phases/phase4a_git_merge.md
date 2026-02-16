# Phase 4a: Git Flow & Squash Merge

Git operations for merging completed Stories into develop branch. Executed after Stage 3 PASS verdict from ln-500-story-quality-gate.

## Git Context

All git commands use `git -C {worktree_map[id]}`. Every worker operates in its own worktree with a named feature branch (`feature/{id}-{slug}`).

## Merge Procedure

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
    git worktree remove .worktrees/story-{id} --force
    worktree_map[id] = null
    CONTINUE                           # Skip merge, move to next story
```

**Conflict Handling:**
- Try rebase first (clean linear history)
- Fallback to merge if rebase fails
- On merge conflict → PAUSED, escalate to user, cleanup worktree
- Continue pipeline with remaining stories

### Step 1a: Collect Code Metrics

Capture diff statistics before squash merge for pipeline report.

```
diff_output = git -C {dir} diff --stat develop...HEAD
git_stats[id] = parse_diff_stat(diff_output)
# Result: {lines_added: N, lines_deleted: N, files_changed: N}
# parse_diff_stat extracts numbers from git's "N files changed, N insertions(+), N deletions(-)" summary line
```
### Step 2: Squash Merge into Develop

Merge all feature branch commits into single commit on develop.

```
git -C {dir} checkout develop
git -C {dir} merge --squash feature/{id}-{slug}
git -C {dir} commit -m "{storyId}: {Story Title}"
git -C {dir} push origin develop
```

**Squash Commit Message Format:**
```
{storyId}: {Story Title}
```

Example: `API-457: Implement user authentication endpoint`

### Step 3: Cleanup Worktree

Remove worktree directory after successful merge. Feature branch is preserved for history.

```
git worktree remove .worktrees/story-{id} --force
worktree_map[id] = null
# NOTE: Feature branch feature/{id}-{slug} is NOT deleted — preserved for git history and audit.
```

### Step 4: Context Refresh

**MANDATORY READ:** Reload main SKILL.md to refresh pipeline context after develop push.

Large merges can shift codebase context significantly. Re-reading ensures accurate state for next Story processing.

### Step 5: Append Story Report (with duration data)

Document Story completion in pipeline report.

```
Append to docs/tasks/reports/pipeline-{date}.md:
  ### {storyId}: {storyTitle} — DONE
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

**Report Fields:**
- **stage0-3:** Stage result (same as before)
- **Duration:** `stage_timestamps[id]["stage_N_end"] - stage_timestamps[id]["stage_N_start"]` formatted as Xm Ys
- **Code:** Lines added/deleted and files changed from `git_stats[id]`
- **Details:** Retry/rework/crash counters (0 if smooth execution)
- **Problems:** Aggregated list from all counters (e.g., "1 validation retry, 1 quality cycle")

### Step 6: Verify Kanban + Linear Sync

Ensure kanban board and Linear (if used) reflect Story completion.

```
# Verify kanban
Re-read kanban board → ASSERT Story {id} is in Done section

# Verify Linear sync (if applicable)
IF storage_mode == "linear":
  Read Linear issue via MCP → ASSERT status matches kanban (Done/Completed)
  IF mismatch: Update Linear status to match kanban
  VERIFY assignee, labels
  IF mismatch found: LOG warning but do NOT block pipeline
```

**Sync Policy:**
- Kanban board is source of truth
- Linear mismatches logged but NOT blocking
- Assignee/labels verified for audit trail

## Error Recovery

| Error | Severity | Action |
|-------|----------|--------|
| Rebase conflict | Medium | Fallback to merge |
| Merge conflict | High | PAUSED, escalate, cleanup worktree, skip story |
| Push failure | High | PAUSED, escalate (network/permissions issue) |
| Kanban/Linear mismatch | Low | LOG warning, continue |

## Related Files

- **Message Handlers:** `phase4_handlers.md` (calls this after Stage 3 PASS)
- **Heartbeat:** `phase4_heartbeat.md`
- **Pipeline States:** `pipeline_states.md` (Stage-to-Status mapping)
- **Checkpoint Format:** `checkpoint_format.md`

---
**Version:** 1.0.0
**Last Updated:** 2026-02-14
