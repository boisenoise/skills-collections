---
name: ln-402-task-reviewer
description: L3 Worker. Reviews task implementation for quality, code standards, test coverage. Creates [BUG] tasks for side-effect issues found outside task scope. Sets task Done or To Rework. Usually invoked by ln-400 with isolated context, can also review a specific task on user request.
---

# Task Reviewer

**MANDATORY after every task execution.** Reviews a single task in To Review and decides Done vs To Rework with immediate fixes or clear rework notes.

> **This skill is NOT optional.** Every task executed by ln-401/ln-403/ln-404 MUST be reviewed by ln-402 immediately. No exceptions, no batching, no skipping.

## Purpose & Scope
- **Independent context loading:** Receive only task ID from orchestrator; load full task and parent Story independently (Linear: get_issue; File: Read task file). This isolation ensures unbiased review without executor's assumptions (fresh eyes pattern).
- Check architecture, correctness, configuration hygiene, docs, and tests.
- For test tasks, verify risk-based limits and priority (≤15) per planner template.
- Update only this task: accept (Done) or send back (To Rework) with explicit reasons and fix suggestions tied to best practices.

## Task Storage Mode

| Aspect | Linear Mode | File Mode |
|--------|-------------|-----------|
| **Load task** | `get_issue(task_id)` | `Read("docs/tasks/epics/.../tasks/T{NNN}-*.md")` |
| **Load Story** | `get_issue(parent_id)` | `Read("docs/tasks/epics/.../story.md")` |
| **Update status** | `update_issue(id, state: "Done"/"To Rework")` | `Edit` the `**Status:**` line in file |
| **Add comment** | Linear comment API | Append to task file or kanban |

**File Mode status values:** Done, To Rework (only these two outcomes from review)

## Workflow (concise)
1) **Receive task (isolated context):** Get task ID from orchestrator (ln-400)—NO other context passed. Load all information independently from Linear. Detect type (label "tests" -> test task, else implementation/refactor).
2) **Read context:** Full task + parent Story; load affected components/docs; review diffs if available.
3) **Review checks:**
   - Approach: diff aligned with Technical Approach in Story. If different → rationale documented in code comments.
   - No hardcoded creds/URLs/magic numbers; config in env/config.
   - Error handling: all external calls (API, DB, file I/O) wrapped in try/catch or equivalent. No swallowed exceptions. Layering respected; reuse existing components.
   - Logging: errors at ERROR; auth/payment events at INFO; debug data at DEBUG. No sensitive data in logs.
   - Comments: explain WHY not WHAT; no commented-out code; docstrings on public methods; Task ID present in new code blocks (`// See PROJ-123`).
   - Naming: follows project's existing convention (check 3+ similar files). No abbreviations except domain terms. No single-letter variables (except loops).
   - Docs: if public API changed → API docs updated. If new env var → .env.example updated. If new concept → README/architecture doc updated.
   - Tests updated/run: for impl/refactor ensure affected tests adjusted; for test tasks verify risk-based limits and priority (≤15) per planner template.
4) **AC Validation (MANDATORY for implementation tasks):**
   Load parent Story AC and verify implementation against 4 criteria (see `references/ac_validation_checklist.md`):
   - **AC Completeness:** All AC scenarios covered (happy path + errors + edge cases).
   - **AC Specificity:** Exact requirements met (HTTP codes 200/401/403, timing <200ms, exact messages).
   - **Task Dependencies:** Task N uses ONLY Tasks 1 to N-1 (no forward dependencies on N+1, N+2).
   - **Database Creation:** Task creates ONLY tables in Story scope (no big-bang schema).
   If ANY criterion fails → To Rework with specific guidance from checklist.
5) **Side-Effect Bug Detection (MANDATORY):**
   While reviewing affected code, actively scan for bugs/issues NOT related to current task:
   - Pre-existing bugs in touched files
   - Broken patterns in adjacent code
   - Security issues in related components
   - Deprecated APIs, outdated dependencies
   - Missing error handling in caller/callee functions

   **For each side-effect bug found:**
   - Create new task in same Story (Linear: create_issue with parentId=Story.id; File: create task file)
   - Title: `[BUG] {Short description}`
   - Description: Location, issue, suggested fix
   - Label: `bug`, `discovered-in-review`
   - Priority: based on severity (security → 1 Urgent, logic → 2 High, style → 4 Low)
   - **Do NOT defer** — create task immediately, reviewer catches what executor missed

6) **Agent Review:** Per `shared/references/agent_delegation_pattern.md` §Parallel Aggregation.
   - **Template:** `code_review.md` with `{task_content}` + `{story_content}` from Step 2.
   - **Verdict escalation:** Agent findings with area=security|correctness can escalate Done → To Rework.
   - **Display:** `"Agent Review: codex ({duration}s, {N}), gemini ({duration}s, {N}). Validated: {accepted}/{total}"`
7) **Decision (for current task only):**
   - If only nits and no critical agent findings: apply minor fixes and set Done.
   - If issues remain (own review OR accepted agent suggestions with security/correctness area): set To Rework with comment explaining why (best-practice ref) and how to fix.
   - Side-effect bugs do NOT block current task's Done status (they are separate tasks).
   - **If Done:** commit all uncommitted changes with message referencing task ID: `git add -A && git commit -m "Implement {task_id}: {task_title}"`
8) **Update:** Set task status in Linear; update kanban: if Done → **remove task from kanban** (Done section tracks Stories only, not individual Tasks); if To Rework → move task to To Rework section; add review comment with findings/actions. If side-effect bugs created, mention them in comment. Include agent review summary in comment.

## Critical Rules
- One task at a time; side-effect bugs → separate [BUG] tasks (not scope creep).
- Zero tolerance: fix now or send back with guidance. Never mark Done with unresolved in-scope issues.
- Test-task violations (limits/priority ≤15) → To Rework.
- Keep task language (EN/RU) in edits/comments.

## Definition of Done
- Steps 1-8 completed: context loaded, review checks passed, AC validated, side-effect bugs created, agent review done, decision applied.
- If Done: changes committed with task ID; task removed from kanban. If To Rework: task moved with fix guidance.
- Review comment posted (findings + agent summary + [BUG] list if any).

## Reference Files
- **[MANDATORY] Problem-solving approach:** `shared/references/problem_solving.md`
- **AC validation rules:** `shared/references/ac_validation_rules.md`
- AC Validation Checklist: `references/ac_validation_checklist.md` (4 criteria: Completeness, Specificity, Dependencies, DB Creation)
- Agent review prompt: `shared/agents/prompt_templates/code_review.md`
- Agent review schema: `shared/agents/schemas/code_review_schema.json`
- Agent delegation: `shared/references/agent_delegation_pattern.md`
- Kanban format: `docs/tasks/kanban_board.md`

---
**Version:** 5.0.0 (BREAKING: Added Agent Review step 6 with parallel codex+gemini aggregation. Commit on Done. AC Validation step 4.)
**Last Updated:** 2026-02-07
