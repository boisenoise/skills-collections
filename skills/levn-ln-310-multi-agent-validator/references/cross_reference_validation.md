# Cross-Reference Validation (Criteria #25-#26)

<!-- SCOPE: Cross-Story overlap and duplication criteria #25-#26 ONLY. Contains AC overlap detection, task duplication checks. -->
<!-- DO NOT add here: Story dependencies → dependency_validation.md, risk → risk_validation.md -->

Detailed rules for cross-Story overlap detection and task deduplication within an Epic.

---

## Criterion #25: AC Cross-Story Overlap

**Check:** Story AC doesn't overlap or conflict with active sibling Stories in same Epic

**Penalty:** MEDIUM (3 points) for overlap / CRITICAL (10 points) for conflict

**Cap:** Max 1 CRITICAL = 10 points (report all conflicts, score only worst)

**Skip When:**
- Epic has only 1 Story (no siblings)
- All sibling Stories are Done/Canceled
- Story not part of any Epic

---

## Detection Algorithm #25

### Step 1: Load Sibling Stories

```
siblings = list_issues(project=Epic.id, label="user-story")
           .filter(status IN [Backlog, Todo, In Progress])
           .filter(id != current_story.id)

IF siblings.count == 0 → PASS (skip check)
```

### Step 2: Structured Traceability (Primary Signal — scored)

Compare current Story against each sibling using structured data:

| Signal | Method | Match = Overlap |
|--------|--------|-----------------|
| AC IDs | Extract AC identifiers (AC1, AC2...) from both Stories | Same AC ID in both Stories |
| Affected Components | Parse `## Affected Components` sections from Tasks | Same file path or component in both Stories' tasks |
| Dependency targets | Parse `## Dependencies` sections | Both Stories depend on or block same Story |
| Implementation file paths | Extract file paths from Implementation Plan | Same file modified by both Stories' tasks |

**Overlap detected:** ≥2 structural signals match → MEDIUM (3 points), add overlap note to Story.

### Step 3: Conflict Detection (scored)

For Stories with structural overlap, compare AC content:

```
FOR EACH overlapping_ac_pair:
  IF same Given + same When + DIFFERENT Then:
    → CRITICAL (10 points)
    → FLAG for human resolution
```

**Example conflict:**
- Story A: "Given valid token, When GET /users, Then return paginated list"
- Story B: "Given valid token, When GET /users, Then return full list with cache"
→ Same precondition + action, conflicting outcomes = CRITICAL

### Step 4: Keyword Overlap (Fallback — advisory only, NOT scored)

If no structural overlap detected, run keyword fallback:

```
FOR EACH sibling:
  ac_keywords_current = extract_keywords(current.ac_text)
  ac_keywords_sibling = extract_keywords(sibling.ac_text)
  overlap = intersection(ac_keywords_current, ac_keywords_sibling)
  overlap_ratio = overlap.count / min(ac_keywords_current.count, ac_keywords_sibling.count)

  IF overlap_ratio > 0.70:
    → WARNING note in audit report (no penalty)
    → "Advisory: high keyword similarity with Story {sibling.id} — review manually"
```

**Why advisory-only:** Keyword overlap produces false positives on formulaic text (common verbs, domain terms, template phrases). Structured traceability is more reliable.

---

## Auto-fix Actions #25

1. **Overlap (MEDIUM):** Add note to Story description:
   ```markdown
   > [!NOTE]
   > **Cross-Reference:** Overlapping scope detected with Story {sibling.id} ({sibling.title})
   > - Shared components: {list}
   > - Review for potential consolidation or scope boundary clarification
   ```

2. **Conflict (CRITICAL):** FLAG only (human resolution required):
   ```markdown
   > [!WARNING]
   > **CRITICAL: AC Conflict** with Story {sibling.id}
   > - This Story: "{ac_text}"
   > - Sibling: "{sibling_ac_text}"
   > - Same Given/When, different Then — resolve before implementation
   ```

---

## Criterion #26: Task Cross-Story Duplication

**Check:** Tasks don't duplicate sibling Stories' tasks

**Penalty:** LOW (1 point per duplication, max 3)

**Skip When:**
- Epic has only 1 Story (no siblings)
- All sibling Stories have no tasks yet
- Story not part of any Epic

---

## Detection Algorithm #26

### Step 1: Load Sibling Task Metadata

```
FOR EACH active sibling Story:
  sibling_tasks = list_issues(parentId=sibling.id)
  Extract: title, Affected Components (file paths)
```

### Step 2: Structured Match (Primary — scored)

| Signal | Method | Match = Duplication |
|--------|--------|---------------------|
| Affected Components | Parse `## Affected Components` from each task | Same file paths in both tasks |
| Implementation targets | Extract modified files from Implementation Plan | Same files modified |

**Duplication detected:** ≥2 file paths shared between tasks across Stories → LOW (1 point per match, max 3).

### Step 3: Title Keyword Overlap (Fallback — advisory only)

```
FOR EACH current_task vs sibling_task:
  title_overlap = keyword_overlap(current_task.title, sibling_task.title)
  IF title_overlap > 0.80:
    → WARNING note (no penalty)
    → "Advisory: task '{current_task.title}' similar to '{sibling_task.title}' in Story {sibling.id}"
```

**Human decides:** Duplication warnings are informational. No auto-delete. Creator reviews and decides whether to merge, split, or keep as-is.

---

## Auto-fix Actions #26

Add advisory note to duplicated tasks:
```markdown
> [!NOTE]
> **DRY Warning (Cross-Story):** Similar task exists in Story {sibling.id}
> - Sibling task: "{sibling_task.title}"
> - Shared files: {list}
> - Review for potential consolidation
```

---

## Execution Order

**Group 6b: Cross-Reference (#25-#26) runs after Dependencies, before Risk**

**Rationale:**
- Needs all Stories loaded and structured (Phase 2)
- Needs dependencies resolved (#18-#19) to avoid double-counting
- Must run before Risk (#20) since overlap may indicate risk
- Must run before Traceability (#16-#17) since overlap notes may affect mapping

**Sequence:**
```
Phase 4 Groups 1-6 complete:
  - Structural (#1-#4, #24)
  - Standards (#5)
  - Solution (#6, #21)
  - Workflow (#7-#13)
  - Quality (#14-#15)
  - Dependencies (#18-#19, #19b)

→ Group 6b: Cross-Reference (#25-#26) runs
  - Load sibling Stories
  - Check AC overlap (structured traceability first)
  - Check task duplication (structured match first)

→ Group 7: Risk (#20) runs
```

---

## Integration with Other Criteria

**Criterion #18 (Story Dependencies):**
- #18 checks sequential execution order
- #25 checks content overlap/conflict
- Complementary: Story can have valid sequential deps AND conflicting AC

**Criterion #11 (YAGNI):**
- #11 checks tasks map to Story's own AC
- #26 checks tasks don't duplicate other Stories' tasks
- Different scope: internal vs cross-Story

**ln-301 DRY Check:**
- ln-301 checks codebase for existing implementations
- #26 checks sibling Stories for task duplication
- Both DRY-oriented but different scopes (code vs plan)

---

**Version:** 1.0.0
**Last Updated:** 2026-03-08
