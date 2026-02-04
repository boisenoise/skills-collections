# AC Validation Checklist

<!-- SCOPE: AC validation criteria for task review (#4, #9, #17, #19). References ln-310 validation files. -->
<!-- DO NOT add here: Code quality checks → ln-402 SKILL.md step 3, Story dependencies → ln-500 -->

Criteria for validating task implementation against Story Acceptance Criteria.

---

## Criterion #1: AC Completeness

**Check:** Implementation covers ALL AC scenarios from Story

**Reference:** [ln-310-story-validator/references/structural_validation.md](../../ln-310-story-validator/references/structural_validation.md) criterion #4 (lines 40-70)

**Quick Check:**
- ✅ Happy Path (1-2 AC) - main success scenarios implemented
- ✅ Error Handling (1-2 AC) - invalid inputs, auth failures handled
- ✅ Edge Cases (1 AC) - boundary conditions, special states covered

**Verdict:**
- **To Rework** if ANY AC scenario missing from implementation

---

## Criterion #2: AC Specificity

**Check:** Implementation matches EXACT AC requirements (HTTP codes, timing, messages)

**Reference:** [ln-310-story-validator/references/structural_validation.md](../../ln-310-story-validator/references/structural_validation.md) criterion #4 (lines 71-95)

**Quick Check:**
- ✅ HTTP codes match AC (200, 201, 400, 401, 403, 404, 500)
- ✅ Response times meet AC (<200ms, <1s, <5s)
- ✅ Error messages exact match ("Invalid credentials", "Token expired")

**Example:**
```markdown
AC: "Given invalid token, When validate, Then 401 error + 'Invalid token'"

✅ GOOD: return Response({"error": "Invalid token"}, status=401)
❌ BAD: return Response({"error": "Error"}, status=500)  // Wrong code + generic message
```

**Verdict:**
- **To Rework** if generic implementation instead of specific requirements

---

## Criterion #3: Task Dependencies (No Forward Deps)

**Check:** Task N does NOT depend on Tasks N+1, N+2 (sequential order)

**Reference:** [ln-310-story-validator/references/dependency_validation.md](../../ln-310-story-validator/references/dependency_validation.md) criterion #19 (lines 53-100)

**Quick Check:**
- ✅ Task uses ONLY previous Tasks (1 to N-1)
- ❌ Task references features from FUTURE Tasks (N+1, N+2)

**Example:**
```markdown
❌ WRONG: Task 2 "Validate token" calls refresh_token_flow() from Task 3
✅ RIGHT: Task 2 uses only generate_keys() from Task 1
```

**Verdict:**
- **To Rework** if forward dependency detected

---

## Criterion #4: Database Creation Principle

**Check:** Task creates ONLY tables mentioned in Story scope (incremental schema)

**Reference:** [ln-310-story-validator/references/workflow_validation.md](../../ln-310-story-validator/references/workflow_validation.md) criterion #9 (lines 85-103)

**Quick Check:**
- ✅ Story "User Registration" → Task creates Users table ONLY
- ❌ Story "User Registration" → Task creates Users + Products + Orders (big-bang violation)

**Example:**
```sql
-- Story 1.1: User Registration
❌ WRONG: CREATE TABLE users, products, orders, payments  -- Premature tables
✅ RIGHT: CREATE TABLE users  -- Only what this Story needs
```

**Verdict:**
- **To Rework** if task creates tables for future Stories

---

## Execution in ln-402 Review

**Integration Point:** Add to review checks (SKILL.md step 3) AFTER existing checks, BEFORE decision (step 5)

**Order:**
1. Existing checks (approach, hardcoded values, error handling, logging, comments, naming, docs, tests)
2. **AC Completeness** - all scenarios covered?
3. **AC Specificity** - exact HTTP codes/messages/timing?
4. **Task Dependencies** - no forward deps?
5. **Database Creation** - schema scope correct?
6. Decision (Done vs To Rework)

**Verdict Logic:**
- If ALL 4 criteria pass → Continue to Decision (step 5)
- If ANY criterion fails → To Rework with specific guidance

---

## Skip Validation When

- Task type = test (label "tests") - tested by ln-404/ln-510, not AC validation
- Task has no parent Story (orphan) - warn user, skip validation
- Story has no AC section - warn user, suggest fixing Story first

---

**Version:** 1.0.0
**Last Updated:** 2026-02-03
