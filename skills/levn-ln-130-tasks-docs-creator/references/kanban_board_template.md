# Task Navigation

<!-- SCOPE: Quick navigation to active tasks. Links point to Linear (if provider=linear) or local files (if provider=file). Per docs/tools_config.md. -->
<!-- DO NOT add here: task descriptions, implementation notes, workflow rules → tasks/README.md -->

> **Last Updated**: [YYYY-MM-DD] (Hierarchical format: Status → Epic → Story → Tasks)

---

## Provider Configuration

**Task provider:** Per `docs/tools_config.md` → Task Management → Provider

<!-- IF provider=linear: fill Linear Configuration below. IF provider=file: delete Linear Configuration, keep only Common Configuration. -->

### Linear Configuration (only when provider=linear)

| Variable | Value | Description |
|----------|-------|-------------|
| **Team ID** | [TEAM_NAME] | Linear team name |
| **Team UUID** | [TEAM_UUID] | Team UUID for API calls |
| **Team Key** | [TEAM_KEY] | Short key for issues |
| **Workspace URL** | [WORKSPACE_URL] | Linear workspace |

**Quick Access (Linear only):**
- [Backlog]([WORKSPACE_URL]/team/[TEAM_KEY]/backlog)
- [Active Sprint]([WORKSPACE_URL]/team/[TEAM_KEY]/active)

### Common Configuration

| Variable | Value | Description |
|----------|-------|-------------|
| **Next Epic Number** | 1 | Next available Epic number |

---

### Epic Story Counters

| Epic | Last Story | Next Story | Last Task | Next Task |
|------|------------|------------|-----------|-----------|
| Epic 0 | - | US001 | - | T001 |
| Epic 1+ | - | US001 | - | T001 |

> [!NOTE]
> Story numbering: US001+ per Epic. Task numbering: T001+ per Story.

---

## Work in Progress

**Format:** Status → Epic → Story → Tasks hierarchy. Epic headers = no indent. Stories = 2-space indent. Tasks = 4-space indent.

**Important:** Stories without tasks ONLY in Backlog/Postponed with note: `_(tasks not created yet)_`

**Critical:** Done/Postponed sections contain ONLY Stories (no Tasks).

<!-- Links below: use Linear URLs (provider=linear) or file paths (provider=file) -->

### Backlog

**Epic 0: Common Tasks**

  📖 [US001 Example Story Title](link-or-path)
    _(tasks not created yet)_

**Epic 1: Example Feature Area**

  📖 [US001 Another Example Story](link-or-path)
    - [T001 Example Task](link-or-path)

### Todo

### In Progress

### To Review

### To Rework

### Done (Last 5 stories)

### Postponed

---

## Epics Overview

**Active:**
_No active epics yet_

**Completed:**
_No completed epics yet_

---

## Workflow Reference

| Status | Purpose |
|--------|---------|
| **Backlog** | New items requiring estimation and approval |
| **Postponed** | Deferred for future iterations |
| **Todo** | Approved, ready for development |
| **In Progress** | Active development |
| **To Review** | Awaiting review |
| **To Rework** | Needs fixes |
| **Done** | Completed and approved |

**Manual Statuses:** Canceled, Duplicate

---

## Related Documentation
- [tasks/README.md](./README.md) - Task system workflow and rules
- [docs/tools_config.md](../../tools_config.md) - Provider configuration

---

**Template Version:** 5.0.0 (Provider-neutral: supports Linear and File Mode per tools_config.md)
**Last Updated:** 2026-03-04
