# Tools Configuration

<!-- SCOPE: Available tools, configured providers, detection rules, and troubleshooting ONLY. -->
<!-- DOC_KIND: reference -->
<!-- DOC_ROLE: canonical -->
<!-- READ_WHEN: Read when choosing tools, providers, or fallback chains for project work. -->
<!-- SKIP_WHEN: Skip when you only need project architecture or product requirements. -->
<!-- PRIMARY_SOURCES: docs/tools_config.md, docs/README.md -->

## Quick Navigation

| Need | Read |
|------|------|
| Documentation map | [README.md](README.md) |
| Standards | [documentation_standards.md](documentation_standards.md) |
| Task workflow | [tasks/README.md](tasks/README.md) |

## Agent Entry

- Purpose: Canonical reference for configured tools and fallback chains.
- Read when: You need to know which provider or tool path to use.
- Skip when: Tool choice is irrelevant to the current task.
- Canonical: Yes.
- Read next: The relevant workflow doc that uses the tool.
- Primary sources: `docs/tools_config.md`, `docs/README.md`.

## Task Management

| Setting | Value |
|---------|-------|
| **Provider** | {{TASK_PROVIDER}} |
| **Status** | {{TASK_STATUS}} |
| **Team ID** | {{TEAM_ID}} |
| **Fallback** | file (`docs/tasks/epics/`) |

## Research

| Setting | Value |
|---------|-------|
| **Provider** | {{RESEARCH_PROVIDER}} |
| **Fallback chain** | {{RESEARCH_CHAIN}} |
| **Status** | {{RESEARCH_STATUS}} |

## File Editing

Follow `shared/references/mcp_tool_preferences.md` for file-editing tool selection.

## External Agents

| Agent | Status | Comment |
|-------|--------|---------|
| codex | {{CODEX_STATUS}} | {{CODEX_COMMENT}} |
| gemini | {{GEMINI_STATUS}} | {{GEMINI_COMMENT}} |

## Git

| Setting | Value |
|---------|-------|
| **Worktree** | {{GIT_WORKTREE}} |
| **Branch strategy** | {{GIT_STRATEGY}} |

## Maintenance

**Update Triggers:**
- When configured providers change
- When fallback chains change
- When tool availability or health-check logic changes

**Verification:**
- [ ] Provider names match actual configured tools
- [ ] Fallback chains are still valid
- [ ] External agent status detection remains accurate

**Last Updated:** {{DATE}}
