---
name: ln-002-best-practices-researcher
description: Research best practices via MCP Ref/Context7 and create documentation (guide/manual/ADR). Single research, multiple output types.
---

# Best Practices Researcher

Research industry standards and create project documentation in one workflow.

## Purpose & Scope
- Research via MCP Ref + Context7 for standards, patterns, versions
- Create 3 types of documents from research results:
  - Guide: Pattern documentation (Do/Don't/When table)
  - Manual: API reference (methods/params/doc links)
  - ADR: Architecture Decision Record (Q&A dialog)
- Return document path for linking in Stories/Tasks

## Phase 0: Stack Detection

**Objective**: Identify project stack to filter research queries and adapt output.

**Detection:**

| Indicator | Stack | Query Prefix | Official Docs |
|-----------|-------|--------------|---------------|
| `*.csproj`, `*.sln` | .NET | "C# ASP.NET Core" | Microsoft docs |
| `package.json` + `tsconfig.json` | Node.js | "TypeScript Node.js" | MDN, npm docs |
| `requirements.txt`, `pyproject.toml` | Python | "Python" | Python docs, PyPI |
| `go.mod` | Go | "Go Golang" | Go docs |
| `Cargo.toml` | Rust | "Rust" | Rust docs |
| `build.gradle`, `pom.xml` | Java | "Java" | Oracle docs, Maven |

**Usage:**
- Add `query_prefix` to all MCP search queries
- Link to stack-appropriate official docs

## When to Use
- ln-310-story-validator detects missing documentation
- Need to document a pattern, library, or decision
- Replaces: ln-321-guide-creator, ln-322-adr-creator, ln-323-manual-creator

## Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| doc_type | Yes | "guide" / "manual" / "adr" |
| topic | Yes | What to document (pattern name, package name, decision title) |
| story_context | No | Story/Task context for relevance |

## Research Tools

**For patterns and standards (guide/manual):**
- `mcp__Ref__ref_search_documentation(query="[topic] RFC standard best practices 2025")` - industry standards
- `mcp__Ref__ref_search_documentation(query="[topic] security vulnerabilities OWASP")` - security checks

**For library versions (manual):**
- `mcp__context7__resolve-library-id(libraryName="[topic]")` -> get Context7 ID
- `mcp__context7__get-library-docs(context7CompatibleLibraryID="...", topic="version changelog")` - current versions
- `WebSearch(query="[topic] latest stable version 2025")` - version verification

**Time-box:** 5-10 minutes for research; skip if topic is trivial

## Workflow by doc_type

### doc_type="guide" (Pattern Guide)

**Purpose:** Document a reusable pattern with Do/Don't/When table.

**Workflow:**
1) **Research:** Call `ref_search_documentation(query="[topic] best practices pattern 2025")`; extract principle, 2-3 do/don'ts, sources with dates
2) **Generate:** Fill 6 sections from guide_template.md:
   - SCOPE tags, Principle, Our Implementation, Patterns table (Do/Don't/When), Sources, Related + Last Updated
   - 300-500 words; no code snippets
3) **Validate:** Ensure SCOPE tags, sources dated (>=2025), patterns table present, POSIX ending
4) **Save:** Assign next number, write `docs/reference/guides/NN-[topic-slug].md`; return path

**Output:** Guide file path for linking in Technical Notes

### doc_type="manual" (API Manual)

**Purpose:** Document a package/library API reference.

**Workflow:**
1) **Research:** Call `mcp__context7__get-library-docs(topic="[detected_stack.query_prefix] [topic]")`; extract methods, params (type/required/default), returns, exceptions
2) **Generate:** Fill sections from manual_template.md:
   - Package info, Overview, Methods (signature/params table/returns), Config table, Limitations, Version notes, Related + Last Updated
   - 300-500 words; neutral factual tone; NO CODE - use doc links instead
3) **Validate:** Ensure SCOPE tags, version in filename, stack-appropriate doc links, POSIX ending
4) **Save:** Write `docs/reference/manuals/[package]-[version].md`; return path

**Output:** Manual file path for linking in Technical Notes

### doc_type="adr" (Architecture Decision Record)

**Purpose:** Document an architecture decision through Q&A dialog.

**Workflow:**
1) **Detect number:** Scan `docs/reference/adrs/` for existing ADRs, pick next zero-padded number
2) **Dialog (5 questions):**
   - Q1: Title of the decision?
   - Q2: Category (Strategic/Technical)?
   - Q3: Context - what problem are we solving?
   - Q4: Decision + Rationale - what did we decide and why?
   - Q5: Alternatives (2 rows with pros/cons/rejection reason)?
3) **Generate:** Fill Nygard format from adr_template.md:
   - Title, Date, Status, Category, Decision Makers, Context, Decision, Rationale, Alternatives table, Consequences, Related
   - 300-500 words
4) **Validate:** Ensure SCOPE tags, ISO date, status field, POSIX ending
5) **Save:** Write `docs/reference/adrs/adr-NNN-[slug].md`; return path

**Output:** ADR file path; remind user to reference in architecture.md if needed

## Critical Rules

**NO_CODE_EXAMPLES (ALL document types):**

| Forbidden | Allowed |
|-----------|---------|
| Code snippets | Tables (params, config, alternatives) |
| Implementation examples | ASCII-схемы, Mermaid diagrams |
| Code blocks >1 line | Method signatures (1 line inline) |
| | Links to official docs |

**Format Priority (STRICT):**
```
┌───────────────────────────────────────────────┐
│ 1. TABLES + ASCII-схемы  ←── ПРИОРИТЕТ        │
│    Params, Config, Alternatives, Flows        │
├───────────────────────────────────────────────┤
│ 2. СПИСКИ (только перечисления)               │
│    Enumeration items, file lists, tools       │
├───────────────────────────────────────────────┤
│ 3. ТЕКСТ (крайний случай)                     │
│    Только если нельзя выразить таблицей       │
└───────────────────────────────────────────────┘
```

| Content Type | Format |
|--------------|--------|
| Parameters | Table: Name \| Type \| Required \| Default |
| Configuration | Table: Option \| Type \| Default \| Description |
| Alternatives | Table: Alt \| Pros \| Cons \| Why Rejected |
| Patterns | Table: Do \| Don't \| When |
| Workflow | ASCII-схема: `A → B → C` |

**Other Rules:**
- Research ONCE per invocation; reuse results
- Cite sources with versions/dates (>=2025)
- One pattern per guide; one decision per ADR; one package per manual
- Preserve language (EN/RU) from story_context
- Link to stack-appropriate docs (Microsoft for .NET, MDN for JS, etc.)
- Do not create if target directory missing (warn instead)

## Definition of Done
- Research completed (standards/patterns/versions extracted) - for guide/manual
- Dialog completed (5 questions answered) - for ADR
- Document generated with all required sections; no placeholders
- Standards validated (SCOPE, maintenance, POSIX)
- File saved to correct directory with proper naming
- Path returned; README updated if placeholder present

## Reference Files
- Guide template: `shared/templates/guide_template.md`
- Manual template: `shared/templates/manual_template.md`
- ADR template: `shared/templates/adr_template.md`
- Standards: `docs/DOCUMENTATION_STANDARDS.md` (if exists)

---
**Version:** 3.0.0
**Last Updated:** 2025-12-23
