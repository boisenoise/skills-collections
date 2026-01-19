# Epic Replan Workflow

Reference file for ln-210-epic-coordinator Phase 5b (REPLAN MODE).

## When Triggered

Phase 3 determined Count ≥ 1 (existing Epics found in kanban_board.md Epic Story Counters).

## Process

### Step 1: Load Existing Epics

- Read Epic Story Counters table from kanban_board.md
- For each Epic row: load Epic from Linear via `get_project(id)`
- Load FULL description (Goal, Scope In/Out, Success Criteria, Risks, Phases)
- Note Epic status (active/archived)
- **Total:** N existing Epics

### Step 2: Compare IDEAL Plan vs Existing

- **Match by goal:** Fuzzy match Epic goals + domain names
- **Identify operations needed:**
  - **KEEP:** Epic in IDEAL + existing, goals unchanged → No action
  - **UPDATE:** Epic in IDEAL + existing, scope/criteria changed → Update description
  - **OBSOLETE:** Epic in existing, NOT in IDEAL → Archive (state="archived")
  - **CREATE:** Epic in IDEAL, NOT in existing → Create new

### Step 3: Categorize Operations

```
✅ KEEP (N Epics): No changes needed
- Epic 5: User Management
- Epic 6: Payment Processing

🔧 UPDATE (M Epics): Scope or criteria changed
- Epic 7: Reporting (Scope modified: add real-time dashboards)
- Epic 8: Notifications (Success Criteria: add email delivery tracking)

❌ OBSOLETE (K Epics): No longer in initiative scope
- Epic 9: Legacy Data Migration (removed from scope)

➕ CREATE (L Epics): New domains added
- Epic 17: Analytics Engine (new initiative requirement)
```

### Step 4: Show Replan Summary

- Display operations for all Epics
- Show diffs for UPDATE operations (before/after Scope, Criteria)
- Show warnings for edge cases:
  - ⚠️ "Epic 7 has 5 Stories In Progress - cannot auto-archive, manual review needed"
- Total operation count

### Step 5: User Confirmation

- Wait for user to type "confirm"
- If user provides feedback → Adjust operations and show updated summary

### Step 6: Execute Operations

- **KEEP:** Skip (no Linear API calls)
- **UPDATE:** Call `update_project(id, description=new_description)` (if no Stories In Progress)
- **OBSOLETE:** Call `update_project(id, state="archived")` (if no Stories In Progress)
- **CREATE:** Call `create_project()` (same as Phase 5a Step 3) + update kanban_board.md

### Step 7: Update kanban_board.md

- Remove OBSOLETE Epics from Epic Story Counters table
- Update modified Epics (UPDATE operations) - preserve Story counters
- Add new Epics (CREATE operations) to Epic Story Counters
- Update Epics Overview section (move archived to Archived section)

## Output

Summary message with operation results + affected Epic URLs

## Important Constraints

- **Never auto-update/archive Epics with Stories In Progress** (show warnings only)
- **Never delete Epics:** Use state="archived" to preserve history
- **Always require user confirmation** before executing operations

---

## Definition of Done (REPLAN)

- [ ] Existing Epics loaded from Linear
- [ ] IDEAL plan compared against existing
- [ ] Operations categorized (KEEP/UPDATE/OBSOLETE/CREATE)
- [ ] User confirmed operations (CONTROL POINT 2)
- [ ] Operations executed in Linear
- [ ] kanban_board.md updated (removed OBSOLETE, added CREATE)
- [ ] Summary displayed with affected Epic URLs

---

**Version:** 1.0.0
**Last Updated:** 2025-12-12
