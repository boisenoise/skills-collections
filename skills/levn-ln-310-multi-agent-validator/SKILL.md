---
name: ln-310-multi-agent-validator
description: "Validates Stories/Tasks or context via parallel multi-agent review (Codex + Gemini). Merges findings, debates, applies fixes. GO/NO-GO verdict."
license: MIT
---

> **Paths:** File paths (`shared/`, `references/`, `../ln-*`) are relative to skills repo root. If not found at CWD, locate this SKILL.md directory and go up one level for repo root.

# Multi-Agent Validator

Validates Stories/Tasks (mode=story) or arbitrary context (mode=context) with parallel multi-agent review and critical verification.

## Inputs

| Input | Required | Source | Description |
|-------|----------|--------|-------------|
| `storyId` | mode=story | args, git branch, kanban, user | Story to process |
| `context {files}` | mode=context | args | File paths to review |
| `identifier` | No | args or auto | Short label for file naming (default: `review_YYYYMMDD_HHMMSS`) |
| `focus` | No | args | Areas to focus on (default: all) |
| `review_title` | No | args | Human-readable title (default: `"Context Review"`) |
| `tech_stack` | No | args or auto-detect | Technology stack override (e.g., `"Python FastAPI"`). Auto-detected if not provided |

**Mode detection:** `"context {file1} {file2}..."` → mode=context. Anything else → mode=story.
**Resolution (mode=story):** Story Resolution Chain. **Status filter:** Backlog

## Purpose & Scope

- **mode=story:** Validate Story plus child Tasks against industry standards and project patterns. Calculate Penalty Points, auto-fix violations, delegate to ln-002 for documentation. Approve Story (Backlog -> Todo).
- **mode=context:** Review plans, documents, architecture proposals via multi-agent review + MCP Ref research. Advisory output only (no status changes).
- **Both modes:** Launch external agents (Codex + Gemini) in parallel with own validation. Merge findings, critically verify, debate, apply accepted changes.
- Support Plan Mode: show audit results, wait for approval, then fix

## When to Use

- **mode=story:** Reviewing Stories before approval (Backlog -> Todo), validating implementation path, ensuring standards fit
- **mode=context:** Reviewing plans, decisions, documents, architecture proposals for independent second opinion
- Optimizing or correcting proposed approaches with multi-agent verification

## Penalty Points System

**Goal:** Quantitative assessment of Story/Tasks quality. Before score = raw quality; After score = post-fix quality.

| Severity | Points | Description |
|----------|--------|-------------|
| CRITICAL | 10 | RFC/OWASP/security violations |
| HIGH | 5 | Outdated libraries, architecture issues |
| MEDIUM | 3 | Best practices violations |
| LOW | 1 | Structural/cosmetic issues |

**Workflow:**
1. Audit: Calculate penalty points for all 27 criteria (Before)
2. Fix: Auto-fix fixable violations; FLAGGED items keep their penalty
3. Report: Before → After (0 if all fixed; >0 if FLAGGED remain)

## Mode Detection

Detect operating mode at startup:

**Plan Mode Active:**
- Phase 1-2: Full audit (discovery + research + penalty calculation)
- Phase 3: Show results + fix plan -> WAIT for user approval
- Phase 4-6: After approval -> execute fixes

**Normal Mode:**
- Phase 1-6: Standard workflow without stopping
- Automatically fix and approve

## Plan Mode: Progress Tracking with TodoWrite

When operating in any mode, skill MUST create detailed todo checklist tracking ALL phases and steps.

**Rules:**
1. Create todos IMMEDIATELY before Phase 1
2. Each phase step = separate todo item
3. Mark `in_progress` before starting step, `completed` after finishing

**Todo Template (~21 items):**

```
Phase 1: Discovery & Loading
  - Auto-discover configuration (Team ID, docs)
  - Load Story metadata (ID, title, status, labels)
  - Load Tasks metadata (1-8 implementation tasks)

Phase 2: Research & Audit
  - Extract technical domains from Story/Tasks
  - Delegate documentation creation to ln-002
  - Research via MCP Ref (RFC, OWASP, library versions)
  - Verify technical claims (Anti-Hallucination)
  - Pre-mortem Analysis (complex Stories)
  - Calculate Penalty Points (27 criteria)

Phase 3: Audit Results & Fix Plan
  - Display Penalty Points table and fix plan
  - Wait for user approval (Plan Mode only)

Phase 4: Auto-Fix (11 groups)
  - Fix Structural violations (#1-#4, #24)
  - Fix Standards violations (#5)
  - Fix Solution violations (#6, #21)
  - Fix Workflow violations (#7-#13)
  - Fix Quality violations (#14-#15)
  - Fix Dependencies violations (#18-#19/#19b)
  - Fix Cross-Reference violations (#25-#26)
  - Fix Risk violations (#20)
  - Fix Pre-mortem violations (#27)
  - Fix Verification violations (#22)
  - Fix Traceability violations (#16-#17)

Phase 1b: Agent Launch (mode=story)
  - Health check: agent availability
  - Build prompt from review_base.md + modes/story.md (per shared workflow "Step: Build Prompt")
  - Launch codex-review + gemini-review as background tasks

Phase 1b: Agent Launch (mode=context)
  - Health check: agent availability
  - Build prompt from review_base.md + modes/context.md (per shared workflow "Step: Build Prompt")
  - Launch codex-review + gemini-review as background tasks

Phase 5: Merge + Critical Verification (MANDATORY)
  - Wait for agent results (process-as-arrive)
  - Re-read lines modified in Phase 4 auto-fix (agents saw pre-fix state)
  - Dedup against Claude's findings + review history
  - Critical Verification + Debate per shared workflow
  - Apply accepted suggestions
  - Save review summary to .agent-review/review_history.md

Phase 6: Approve & Notify (mode=story only)
  - Set Story/Tasks to Todo status in Linear
  - Update kanban_board.md with APPROVED marker
  - Add Linear comment with validation summary
  - Display tabular output to terminal
```

## Workflow

### Phase 0: Tools Config

**MANDATORY READ:** Load `shared/references/tools_config_guide.md`, `shared/references/storage_mode_detection.md`, and `shared/references/input_resolution_pattern.md`

Extract: `task_provider` = Task Management → Provider (`linear` | `file`).

All subsequent phases use `task_provider` to select operations per storage_mode_detection.md.

### Phase 1: Discovery & Loading

**Step 1: Resolve storyId** (per input_resolution_pattern.md):
- IF args provided → use args
- ELSE IF git branch matches `feature/{id}-*` → extract id
- ELSE IF kanban has exactly 1 Story in [Backlog] → suggest
- ELSE → AskUserQuestion: show Stories from kanban filtered by [Backlog]

**Step 2: Configuration & Metadata Loading**
- Auto-discover configuration: Team ID (`docs/tasks/kanban_board.md`), project docs (`CLAUDE.md`), epic from Story.project
- Load metadata only: Story ID/title/status/labels, child Task IDs/titles/status/labels
  - IF `task_provider` = `linear`: `get_issue(storyId)` + `list_issues(parentId=storyId)`
  - IF `task_provider` = `file`: `Read story.md` + `Glob("docs/tasks/epics/*/stories/*/tasks/*.md")`
- Expect 1-8 implementation tasks; record parentId for filtering
- Rationale: keep loading light; full descriptions arrive in Phase 2

### Phase 1b: Agent Launch

**MANDATORY READ:** Load `shared/references/agent_review_workflow.md`, `shared/references/agent_delegation_pattern.md`

**mode=story:**

1) **Health Check** (per shared workflow "Step: Health Check"):
   - Read `docs/environment_state.json` → exclude agents with `disabled: true`
   - Run `python shared/agents/agent_runner.py --health-check` for remaining agents
   - If 0 agents available → skip agent review, proceed with Claude-only validation
2) **Get references:**
   - IF `task_provider` = `linear`: `get_issue(storyId)` → Story URL, `list_issues(parent=storyId)` → Task URLs
   - IF `task_provider` = `file`: Read story.md, Glob tasks → paths
3) **Build prompt:** Assemble from `shared/agents/prompt_templates/review_base.md` + `modes/story.md` (per shared workflow "Step: Build Prompt"), replace `{story_ref}`, `{task_refs}`. Save to `.agent-review/{identifier}_storyreview_prompt.md`
4) **Launch BOTH agents** as background tasks (per shared workflow "Step: Run Agents")

**mode=context:**

1) **Health Check:** same as above
2) **Resolve identifier:** If not provided, generate `review_YYYYMMDD_HHMMSS`
3) **Materialize context (if needed):** If context is from chat → write to `.agent-review/context/{identifier}_context.md`
4) **Build prompt:** Assemble from `shared/agents/prompt_templates/review_base.md` + `modes/context.md` (per shared workflow "Step: Build Prompt"), replace `{review_title}`, `{context_refs}`, `{focus_areas}`. Save to `.agent-review/{identifier}_contextreview_prompt.md`
5) **Launch BOTH agents** as background tasks

Agents now run in background. Claude proceeds to foreground work.

### Foreground: mode=context (skip Phases 2-4, run MCP Ref research instead)

**MANDATORY READ:** Load `references/context_review_pipeline.md` (weight table, stack detection, safety rules) and `shared/references/research_tool_fallback.md`

While agents run in background, Claude performs foreground research:

a) **Load Review Memory** — per shared workflow "Step: Load Review Memory"
b) **Applicability Check** — scan context_files for technology decision signals (infrastructure, API/protocol, security, library/framework choices). No signals → skip MCP Ref, proceed to Phase 5.
c) **Stack Detection** — detect `query_prefix` from: `tech_stack` input > `docs/tools_config.md` > indicator files (*.csproj, package.json, etc.)
d) **Extract Topics (3-5)** — parse context_files for technology decisions, score by weight, take top 3-5
e) **MCP Ref Research** — per `research_tool_fallback.md` chain (Ref → Context7 → WebSearch). Query: `"{query_prefix} {topic} RFC standard best practices {current_year}"`
f) **Compare & Correct** — if MCP Ref contradicts plan statement (high confidence), apply surgical Edit with inline rationale `"(per {RFC/standard}: ...)"`. Max 5 corrections per run. In Plan Mode → output to chat, skip edits until approved.
g) **Save Findings** — write to `.agent-review/context/{identifier}_mcp_ref_findings.md` (per `references/mcp_ref_findings_template.md`). Display: `"MCP Ref: {N} topics validated, {M} corrections, {K} confirmed"`

Then proceed to Phase 5 (Merge).

### Phase 2: Research & Audit (mode=story only)

> **PREREQUISITE:** Phase 1b (Agent Launch) must have completed before Phase 2. If agents were not launched and health check was not run, go back to Phase 1b.

**MANDATORY READ:** Load `references/phase2_research_audit.md` for complete research and audit procedure:
- Domain extraction from Story/Tasks
- Documentation delegation to ln-002 (guides/manuals/ADRs)
- MCP research (RFC/OWASP/library versions via Ref + Context7)
- Anti-Hallucination verification (evidence-based claims)
- Pre-mortem Analysis (Tigers → #20, Elephants → #24)
- Penalty Points calculation (27 criteria, see Auto-Fix Actions Reference in same file)

**Always execute for every Story - no exceptions.**

### Phase 3: Audit Results & Fix Plan

**Display audit results:**
- Penalty Points table (criterion, severity, points, description)
- Total: X penalty points
- Fix Plan: list of fixes for each criterion

**Mode handling:**
- **IF Plan Mode:** Show results + "After your approval, changes will be applied" -> WAIT
- **ELSE (Normal Mode):** Proceed to Phase 4 immediately

### Phase 4: Auto-Fix

**Execute fixes for ALL 27 criteria on the spot.**

- Execution order (11 groups):
  1. **Structural (#1-#4, #24)** — Story/Tasks template compliance + AC completeness/specificity + Assumption Registry
  2. **Standards (#5)** — RFC/OWASP compliance FIRST (before YAGNI/KISS!)
  3. **Solution (#6, #21)** — Library versions, alternative solutions
  4. **Workflow (#7-#13)** — Test strategy, docs integration, size, cleanup, YAGNI, KISS, task order
  5. **Quality (#14-#15)** — Documentation complete, hardcoded values
  6. **Dependencies (#18-#19/#19b)** — Story/Task independence (no forward deps), parallel group validity
  7. **Cross-Reference (#25-#26)** — AC overlap with siblings, task duplication across Stories
  8. **Risk (#20)** — Implementation risk analysis (after dependencies resolved, before traceability)
  9. **Pre-mortem (#27)** — Tiger/Paper Tiger/Elephant classification (complex Stories)
  10. **Verification (#22)** — AC verify methods exist for all task ACs (test/command/inspect)
  11. **Traceability (#16-#17)** — Story-Task alignment, AC coverage quality (LAST, after all fixes)
- Use Auto-Fix Actions table below as authoritative checklist
- Zero out penalty points as fixes applied
- Test Strategy section must exist but remain empty (testing handled separately)

### Phase 5: Merge + Critical Verification (MANDATORY — DO NOT SKIP)

> **MANDATORY STEP:** This phase merges agent results (launched in Phase 1b) with Claude's own findings. Agents were already running in background during Phases 2-4 (mode=story) or during foreground research (mode=context).

**MANDATORY READ:** Load `shared/references/agent_review_workflow.md` (Critical Verification + Debate), `shared/references/agent_review_memory.md`

1) **Wait for agent results** — read result files as they arrive (process-as-arrive pattern)
2) **Parse agent suggestions** from both agents' result files
3) **MERGE:** Claude's own findings (Phase 2-4 violations for mode=story, MCP Ref findings for mode=context) + Agent suggestions
   - If agent suggestion targets lines modified in Phase 4 auto-fix, re-read affected lines before evaluation (agents saw pre-fix state, files are now post-fix)
4) **For EACH agent suggestion:**
   - Dedup against Claude's own findings (skip if already covered)
   - Dedup against review history (skip if already addressed)
   - Claude Evaluation: is it real? Actionable? Applies to our context?
   - MCP Ref enhancement (mode=context): agent suggestion contradicts MCP Ref finding → DISAGREE with citation; aligns → AGREE; not covered → standard evaluation
   - AGREE → accept. DISAGREE → debate (Challenge + Follow-Up per shared workflow)
5) **Apply accepted suggestions:**
   - mode=story → apply to Story/Tasks text
   - mode=context → output to chat as advisory
6) **Save review summary** to `.agent-review/review_history.md`
- If verdict = `SKIPPED` (no agents at health check) → proceed to Phase 6 unchanged
- **Display:** `"Agent Review: codex ({accepted}/{total}), gemini ({accepted}/{total}), {N} suggestions applied"`

### Phase 6: Approve & Notify (mode=story only)

**mode=context:** Skip Phase 6. Return suggestions as advisory output. Done.

- Set Story + all Tasks to Todo; update `kanban_board.md` with APPROVED marker
  - IF `task_provider` = `linear`: `save_issue({id, state: "Todo"})` for Story + each Task
  - IF `task_provider` = `file`: `Edit` `**Status:**` line to `Todo` in story.md + each task file
- **Add validation summary comment:**
  - IF `task_provider` = `linear`: `create_comment({issueId, body})` on Story
  - IF `task_provider` = `file`: `Write` comment to `docs/tasks/epics/.../comments/{ISO-timestamp}.md`
  - Content: Penalty Points table (Before -> After = 0), Auto-Fixes Applied, Documentation Created (via ln-002), Standards Compliance Evidence
- **Display tabular output** (Unicode box-drawing) to terminal with Before/After scores
- **Recommended next step:** `ln-400-story-executor` to start Story execution

## Auto-Fix Actions Reference

**MANDATORY READ:** Load `references/phase2_research_audit.md` for complete 27-criteria table with:
- Structural (#1-#4, #24): Story/Task template compliance, Assumption Registry
- Standards (#5): RFC/OWASP compliance
- Solution (#6, #21): Library versions, alternatives
- Workflow (#7-#13): Test strategy, docs, size, YAGNI/KISS, task order
- Quality (#14-#15): Documentation, hardcoded values
- Dependencies (#18-#19/#19b): No forward dependencies
- Cross-Reference (#25-#26): AC overlap, task duplication across sibling Stories
- Risk (#20): Implementation risk analysis
- Pre-mortem (#27): Tiger/Paper Tiger/Elephant classification
- Traceability (#16-#17): Story-Task alignment, AC coverage

**Maximum Penalty:** 110 points (sum of all 27 criteria; #20 capped at 15; #25 max 1 CRITICAL = 10)

## Final Assessment Model

**Two-stage assessment:** Before (raw audit) and After (post auto-fix).

| Metric | Before | After | Meaning |
|--------|--------|-------|---------|
| **Penalty Points** | Raw audit total | Remaining after fixes | 0 = all fixed; >0 = unfixable items |
| **Readiness Score** | `10 - (Before / 5)` | `10 - (After / 5)` | Quality confidence (1-10) |
| **Anti-Hallucination** | — | VERIFIED / FLAGGED | Technical claims verified |
| **AC Coverage** | — | N/N (target 100%) | All ACs mapped to Tasks |
| **Gate** | — | GO / NO-GO | Final verdict |

### GO/NO-GO Decision

| Gate | Condition |
|------|-----------|
| GO | After Penalty Points = 0 AND no FLAGGED criteria |
| NO-GO | After Penalty Points > 0 OR any criterion FLAGGED as unfixable |

**FLAGGED criteria:** If auto-fix is impossible (MCP Ref unavailable, external dependency), penalty stays — it is NOT zeroed out. User must resolve manually before re-validation.

### Anti-Hallucination Verification

Verify technical claims have evidence:

| Claim Type | Verification |
|------------|--------------|
| RFC/Standard reference | MCP Ref search confirms existence |
| Library version | Context7 query confirms version |
| Security requirement | OWASP/CWE reference exists |
| Performance claim | Benchmark/doc reference |

**Status:** VERIFIED (all claims sourced) or FLAGGED (unverified claims listed)

### Task-AC Coverage Matrix

Output explicit mapping:

```
| AC | Task(s) | Coverage |
|----|---------|----------|
| AC1: Given/When/Then | T-001, T-002 | ✅ |
| AC2: Given/When/Then | T-003 | ✅ |
| AC3: Given/When/Then | — | ❌ UNCOVERED |
```

**Coverage:** `{covered}/{total} ACs` (target: 100%)

## Self-Audit Protocol (Mandatory)

Verify all 27 criteria (#1-#27) from Auto-Fix Actions pass with concrete evidence (doc path, MCP result, Linear update) before proceeding to Phase 6.

## Critical Rules
- All 27 criteria MUST be verified with concrete evidence (doc path, MCP result, Linear update) before Phase 6 (Self-Audit Protocol)
- Fix execution order is strict: Structural -> Standards -> Solution -> Workflow -> Quality -> Dependencies -> Cross-Reference -> Risk -> Pre-mortem -> Verification -> Traceability (standards before YAGNI/KISS)
- If auto-fix succeeds, zero out that criterion's penalty. If auto-fix is impossible (e.g., MCP Ref unavailable, external dependency), mark as FLAGGED with reason — penalty stays, Gate = NO-GO, user must resolve manually
- Test Strategy section must exist but remain empty (testing handled separately by other skills)
- In Plan Mode, MUST stop after Phase 3 and wait for user approval before applying any fixes

## Definition of Done

- Phases 1-6 completed: metadata loaded, research done, penalties calculated, fixes applied, agent review done, Story approved.
- Penalty Points After = 0 (all 27 criteria fixed or none FLAGGED). Readiness Score After = 10.
- Anti-Hallucination: VERIFIED (all claims sourced via MCP).
- AC Coverage: 100% (each AC mapped to ≥1 Task).
- Agent Review: agents launched in background before Phase 2, results merged in Phase 5, suggestions verified + debated, accepted applied (or SKIPPED if no agents).
- Story/Tasks set to Todo; kanban updated; Linear comment with Final Assessment posted.

## Example Workflow

**Story:** "Create user management API with rate limiting"

1. **Phase 1:** Load metadata (5 Tasks, status Backlog)
1b. **Phase 1b:** Health check → launch codex-review + gemini-review in background
2. **Phase 2:**
   - Domain extraction: REST API, Rate Limiting
   - Delegate ln-002: creates Guide-05 (REST patterns), Guide-06 (Rate Limiting)
   - MCP Ref: RFC 7231 compliance, OWASP API Security
   - Context7: Express v4.19 (current v4.17)
   - Penalty Points: 18 total (version=5, missing docs=5, structure=3, standards=5)
3. **Phase 3:**
   - Show Penalty Points table
   - IF Plan Mode: "18 penalty points found. Fix plan ready. Approve?"
4. **Phase 4:**
   - Fix #6: Update Express v4.17 -> v4.19
   - Fix #5: Add RFC 7231 compliance notes
   - Fix #13: Add Guide-05, Guide-06 references
   - Fix #17: Docs already created by ln-002
   - All fixes applied, Penalty Points = 0
5. **Phase 5:** Merge agent results (launched in Phase 1b) + Claude's findings → verify, debate, apply
6. **Phase 6:** Story -> Todo, tabular report

## Template Loading

**Templates:** `story_template.md`, `task_template_implementation.md`

**Loading Logic:**
1. Check if `docs/templates/{template}.md` exists in target project
2. IF NOT EXISTS:
   a. Create `docs/templates/` directory if missing
   b. Copy `shared/templates/{template}.md` → `docs/templates/{template}.md`
   c. Replace placeholders in the LOCAL copy:
      - `{{TEAM_ID}}` → from `docs/tasks/kanban_board.md`
      - `{{DOCS_PATH}}` → "docs" (standard)
3. Use LOCAL copy (`docs/templates/{template}.md`) for all validation operations

**Rationale:** Templates are copied to target project on first use, ensuring:
- Project independence (no dependency on skills repository)
- Customization possible (project can modify local templates)
- Placeholder replacement happens once at copy time

## Reference Files

- **Tools config:** `shared/references/tools_config_guide.md`
- **Storage mode operations:** `shared/references/storage_mode_detection.md`
- **AC validation rules:** `shared/references/ac_validation_rules.md`
- **Plan mode behavior:** `shared/references/plan_mode_pattern.md`
- **Final Assessment:** `references/readiness_scoring.md` (GO/NO-GO rules, Readiness Score calculation)
- **Templates (centralized):** `shared/templates/story_template.md`, `shared/templates/task_template_implementation.md`
- **Local copies:** `docs/templates/` (in target project)
- **Validation Checklists (Progressive Disclosure):**
  - `references/structural_validation.md` (criteria #1-#4)
  - `references/standards_validation.md` (criterion #5)
  - `references/solution_validation.md` (criterion #6)
  - `references/workflow_validation.md` (criteria #7-#13)
  - `references/quality_validation.md` (criteria #14-#15)
  - `references/dependency_validation.md` (criteria #18-#19/#19b)
  - `references/risk_validation.md` (criterion #20)
  - `references/cross_reference_validation.md` (criteria #25-#26)
  - `references/premortem_validation.md` (criterion #27)
  - `references/traceability_validation.md` (criteria #16-#17)
  - `references/domain_patterns.md` (pattern registry for ln-002 delegation)
  - `references/penalty_points.md` (penalty system details)
- **Prevention checklist:** `shared/references/creation_quality_checklist.md` (creator-facing mapping of 27 criteria)
- **MANDATORY READ:** `shared/templates/linear_integration.md`, `shared/references/research_tool_fallback.md`
- **Agent review workflow:** `shared/references/agent_review_workflow.md`
- **Agent delegation pattern:** `shared/references/agent_delegation_pattern.md`
- **Agent review memory:** `shared/references/agent_review_memory.md`
- **Review templates:** `shared/agents/prompt_templates/review_base.md` + `modes/story.md`, `modes/context.md`
- **Challenge template:** `shared/agents/prompt_templates/challenge_review.md`
- **MCP Ref findings template:** `references/mcp_ref_findings_template.md`
- **Context review pipeline:** `references/context_review_pipeline.md` (weight table, stack detection, safety rules for mode=context)

---
**Version:** 7.0.0
**Last Updated:** 2026-02-03
