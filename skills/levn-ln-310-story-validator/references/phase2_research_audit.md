# Phase 2: Research & Audit

**Always execute for every Story - no exceptions.**

## Step 1: Domain Extraction

- Extract technical domains from Story title + Technical Notes + Implementation Tasks
- Load pattern registry from `references/domain_patterns.md`
- Scan Story content for pattern matches via keyword detection
- Build list of detected domains requiring documentation

## Step 2: Documentation Delegation

For EACH detected pattern, delegate to ln-002:

```
Skill(skill="ln-002-best-practices-researcher",
      args="doc_type=[guide|manual|adr] topic='[pattern]'")
```

Receive file paths to created documentation (`docs/guides/`, `docs/manuals/`, `docs/adrs/`, `docs/research/`).

## Step 3: Research via MCP

- Query MCP Ref for industry standards: `ref_search_documentation(query="[topic] RFC OWASP best practices 2025")`
- Query Context7 for library versions: `resolve-library-id` + `query-docs`
- Extract: standards (RFC numbers, OWASP rules), library versions, patterns

## Step 4: Anti-Hallucination Verification

- Scan Story/Tasks for technical claims (RFC references, library versions, security requirements)
- Verify each claim has MCP Ref/Context7 evidence
- Flag unverified claims for correction
- Status: VERIFIED (all sourced) or FLAGGED (list unverified)

## Step 5: Penalty Points Calculation

- Evaluate all 21 criteria against Story/Tasks (see Auto-Fix Actions Reference below)
- Assign penalty points per violation (CRITICAL=10, HIGH=5, MEDIUM=3, LOW=1)
- Calculate total penalty points
- Build fix plan for each violation

# Auto-Fix Actions Reference

Detailed criteria table for Phase 4 auto-fix execution and Phase 2 penalty calculation.

## Structural (#1-#4)

| # | Criterion | What it checks | Penalty | Auto-fix actions |
|---|-----------|----------------|---------|------------------|
| 1 | Story Structure | 8 sections per template | LOW (1) | Add/reorder sections with TODO placeholders; update Linear |
| 2 | Tasks Structure | Each Task has 7 sections | LOW (1) | Load each Task; add/reorder sections; update Linear |
| 3 | Story Statement | As a/I want/So that clarity | LOW (1) | Rewrite using persona/capability/value; update Linear |
| 4 | Acceptance Criteria | Given/When/Then, 3-5 items; each task AC has `verify:` method | MEDIUM (3) | Normalize to G/W/T; add edge cases; generate `verify:` methods for task ACs missing them (test/command/inspect based on AC content); update Linear |

## Standards (#5)

| # | Criterion | What it checks | Penalty | Auto-fix actions |
|---|-----------|----------------|---------|------------------|
| 5 | Standards Compliance | Each technical decision references specific RFC/OWASP/REST standard by number | CRITICAL (10) | Query MCP Ref; update Technical Notes with compliant approach |

## Solution (#6, #21)

| # | Criterion | What it checks | Penalty | Auto-fix actions |
|---|-----------|----------------|---------|------------------|
| 6 | Library & Version | Libraries are latest stable | HIGH (5) | Query Context7; update to recommended versions |
| 21 | Alternative Solutions | Story approach is optimal vs modern alternatives | MEDIUM (3) | Search MCP Ref + web for alternatives; if better option found — add "Alternative Considered" note to Technical Notes with trade-off comparison |

## Workflow (#7-#13)

| # | Criterion | What it checks | Penalty | Auto-fix actions |
|---|-----------|----------------|---------|------------------|
| 7 | Test Strategy | Section exists but empty | LOW (1) | Ensure section present; leave empty (testing handled separately) |
| 8 | Documentation Integration | No standalone doc tasks | MEDIUM (3) | Remove doc-only tasks; fold into implementation DoD |
| 9 | Story Size | 1-8 tasks (3-5 optimal); 3-5h each | MEDIUM (3) | If >8, add TODO; flag task size issues |
| 10 | Test Task Cleanup | No premature test tasks | MEDIUM (3) | Remove test tasks before final; testing appears later |
| 11 | YAGNI | Each Task maps to ≥1 Story AC; no tasks without AC justification | MEDIUM (3) | Move speculative items to Out of Scope unless standards require |
| 12 | KISS | No task requires >3 new abstractions; if >3 → split or simplify | MEDIUM (3) | Simplify unless standards require complexity |
| 13 | Task Order | DB→Service→API→UI | MEDIUM (3) | Reorder Tasks foundation-first |

## Quality (#14-#15)

| # | Criterion | What it checks | Penalty | Auto-fix actions |
|---|-----------|----------------|---------|------------------|
| 14 | Documentation Complete | Pattern docs exist + referenced | HIGH (5) | Delegate to ln-002; add all doc links to Technical Notes |
| 15 | Code Quality Basics | No hardcoded values | MEDIUM (3) | Add TODOs for constants/config/env |

## Traceability (#16-#17)

| # | Criterion | What it checks | Penalty | Auto-fix actions |
|---|-----------|----------------|---------|------------------|
| 16 | Story-Task Alignment | Each Task title contains keyword from Story AC; grep verification | MEDIUM (3) | Add TODO to misaligned Tasks; warn user |
| 17 | AC-Task Coverage | Coverage matrix: each AC row has ≥1 Task; no empty rows | MEDIUM (3) | Add TODO for uncovered ACs; suggest missing Tasks |

## Dependencies (#18-#19)

| # | Criterion | What it checks | Penalty | Auto-fix actions |
|---|-----------|----------------|---------|------------------|
| 18 | Story Dependencies | No forward Story dependencies | CRITICAL (10) | Flag forward dependencies; suggest reorder |
| 19 | Task Dependencies | No forward Task dependencies | MEDIUM (3) | Flag forward dependencies; reorder Tasks |

## Risk (#20)

| # | Criterion | What it checks | Penalty | Auto-fix actions |
|---|-----------|----------------|---------|------------------|
| 20 | Risk Analysis | Unmitigated implementation risks (architecture, errors, scalability, data integrity, integration, SPOF) | HIGH (5) per risk, max 15 | Score via Impact x Probability matrix; add TODO sections for Priority 15-19; FLAG for human review at Priority >= 20; skip at Priority <= 8 |

## Verification Methods (#22)

| # | Criterion | What it checks | Penalty | Auto-fix actions |
|---|-----------|----------------|---------|------------------|
| 22 | AC Verify Methods | Every task AC has `verify:` method (test/command/inspect); at least 1 non-inspect per task | MEDIUM (3) | Generate `verify:` methods based on AC content: HTTP endpoints → command, DB operations → inspect, business logic → test; update Linear |

**Maximum Penalty:** 88 points (sum of all 22 criteria; #20 capped at 15)

---
**Version:** 1.0.0
**Last Updated:** 2026-02-14
