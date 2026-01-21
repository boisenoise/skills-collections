# Structural Validation (Criteria #1-#4)

<!-- SCOPE: Structure and template compliance criteria #1-#4 ONLY. Contains section order, Story statement, AC format rules. -->
<!-- DO NOT add here: Workflow criteria → workflow_validation.md, standards → standards_validation.md -->

Detailed rules for Story/Tasks structure, Story statement, and Acceptance Criteria validation.

---

## Criterion #1: Story Structure (Template Compliance)

**Check:** Story description follows template structure with 8 sections in order

**Penalty:** LOW (1 point)

⚠️ **Important:** Request FULL Story description from Linear (not truncated) to validate all 8 sections.

**Required Sections (in order):**
1. **Story** (As a / I want / So that)
2. **Context** (Current Situation + Desired Outcome)
3. **Acceptance Criteria** (Given-When-Then: Main Scenarios + Edge Cases + Error Handling)
4. **Implementation Tasks** (List with links)
5. **Test Strategy** (empty placeholder, testing planned separately)
6. **Technical Notes** (Architecture Considerations + Integration Points + Performance & Security)
7. **Definition of Done** (Functionality + Testing + Code Quality)
8. **Dependencies** (Depends On + Blocks)

✅ All 8 sections present in correct order
✅ Each section has non-empty content (except Test Strategy - must be empty)
✅ Required subsections present (Context: Current Situation/Desired Outcome)

❌ Missing sections → Add with template placeholders (`_TODO: Fill this section_`)
❌ Sections out of order → Reorder to match template
❌ Empty sections → Add placeholder text

**Auto-fix actions:**
1. Parse current Story description
2. Identify missing/misplaced sections
3. Restructure:
   - Add missing sections with TODO placeholders
   - Reorder sections to match template
   - Add missing subsections (Current Situation, Desired Outcome, etc.)
4. Update Linear issue via `mcp__linear-server__update_issue`
5. Add comment to Linear explaining changes

**Template Reference:** Story template (8 sections structure)

**Skip Fix When:**
- Story in Done/Canceled status
- Story older than 30 days (legacy, don't touch)

---

## Criterion #2: Tasks Structure (Template Compliance - EVERY Task)

**Check:** All child Task descriptions follow template structure

**Penalty:** LOW (1 point per Task)

**Equally Critical:** This check is as important as Story validation (#1). EVERY Task must comply with task_template_implementation.md.

⚠️ **Important:** Request FULL Task description from Linear (not truncated) for EACH Task to validate all 7 sections.

**Required Sections (in order for EACH Task):**
1. **Context** (Current State + Desired State)
2. **Implementation Plan** (Phase 1-3 with checkboxes)
3. **Technical Approach** (Recommended + Why + Patterns + Alternatives)
4. **Acceptance Criteria** (Given-When-Then with checkboxes)
5. **Affected Components** (Implementation + Documentation)
6. **Existing Code Impact** (Refactoring + Tests to Update + Documentation to Update)
7. **Definition of Done** (Checklist)

> [!NOTE]
> Test Strategy removed from Tasks - all tests in Story's final task

✅ All 7 sections present in correct order in EVERY Task
✅ Each section has non-empty content in every Task
✅ Required subsections present in every Task

❌ Missing sections in any Task → Add with template placeholders
❌ Sections out of order in any Task → Reorder to match template

**Auto-fix actions (for each Task with structure violations):**
1. Parse Task description
2. Identify missing/misplaced sections
3. Restructure each Task individually
4. Update Linear issue for each Task via `mcp__linear-server__update_issue`
5. Add comment to Linear for each fixed Task

**Template Reference:** [ln-301-task-creator/references/task_template_implementation.md](../../ln-301-task-creator/references/task_template_implementation.md)

**Skip Fix When:**
- Task in Done/Canceled status
- Task older than 30 days (legacy, don't touch)

---

## Criterion #3: Story Statement (User-Focused)

**Check:** Clear, specific, user-focused (As a / I want / So that)

**Penalty:** LOW (1 point)

✅ **GOOD:** "As a API client, I want to authenticate with OAuth2 tokens, So that users can securely access their data"
❌ **BAD:** "Improve authentication" (vague, no user context)

**Auto-fix actions:**
1. Extract persona from Context section
2. Identify capability from Technical Notes
3. Extract value from Success Metrics (or Context → Desired Outcome)
4. Rewrite Story statement using formula:
   ```
   As a [persona from Context]
   I want to [capability from Technical Notes]
   So that [value from Success Metrics or Desired Outcome]
   ```
5. Update Linear issue via `mcp__linear-server__update_issue`
6. Add comment explaining rewrite

**Example transformation:**
- Before: "Add OAuth support"
- After: "As a API client, I want to authenticate using OAuth 2.0 tokens, So that I can securely access user data without storing passwords"

---

## Criterion #4: Acceptance Criteria (Testable, GWT Format)

**Check:** Specific, testable, Given/When/Then format covering Story goal

**Penalty:** MEDIUM (3 points)

✅ **GOOD:**
- "Given valid OAuth2 token, When API request sent, Then user authenticated and data returned"
- "Given invalid token, When API request sent, Then 401 error returned"

❌ **BAD:** "Authentication should work correctly" (not testable)

**Requirements:**
- 3-5 Acceptance Criteria
- Given/When/Then format
- Cover main scenarios + edge cases + error handling

**Auto-fix actions:**
1. Parse existing AC
2. Convert to Given/When/Then format:
   - **Given:** Preconditions (state, inputs)
   - **When:** Action (user action, API call)
   - **Then:** Expected outcome (success, error)
3. Add missing scenarios:
   - If only positive → add negative (error handling)
   - If only main flow → add edge cases
4. Update Linear issue via `mcp__linear-server__update_issue`
5. Add comment explaining additions

**Example transformation:**
- Before: "User can login", "Login fails with wrong password"
- After:
  1. "Given valid credentials, When user submits login form, Then user is authenticated and redirected to dashboard"
  2. "Given invalid password, When user submits login form, Then 401 error is returned with message 'Invalid credentials'"
  3. "Given account locked, When user submits login form, Then 403 error is returned with message 'Account locked'"
  4. "Given missing email field, When user submits login form, Then 400 error is returned with message 'Email required'"

---

**Version:** 2.0.0
**Last Updated:** 2025-01-07
