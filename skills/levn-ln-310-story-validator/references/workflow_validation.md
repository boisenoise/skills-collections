# Workflow Validation (Criteria #7-#13)

<!-- SCOPE: Workflow validation criteria #7-#13 ONLY. Contains test strategy, KISS/YAGNI, task order, Story size rules. -->
<!-- DO NOT add here: Structural validation → structural_validation.md, traceability → traceability_validation.md -->

Detailed rules for test strategy, documentation integration, Story size, test cleanup, YAGNI, KISS, and task order.

---

## Criterion #7: Test Strategy Section (Empty Placeholder)

**Check:** Test Strategy section exists but is EMPTY (testing planned separately)

**Penalty:** LOW (1 point)

**GOOD:**
```markdown
## Test Strategy

_Testing will be planned in final Task_
```

**BAD:**
```markdown
## Test Strategy

Unit tests:
- Test login() function
- Test token validation
```

**Auto-fix actions:**
1. Check if Test Strategy section exists
2. IF missing -> Add empty section with placeholder
3. IF contains content -> Clear content, add placeholder
4. Update Linear issue via `mcp__linear-server__update_issue`

**Rationale:** Test planner analyzes ALL implementation Tasks to create Risk-Based Test Plan. Premature test planning = incomplete coverage.

---

## Criterion #8: Documentation Integration (No Standalone Doc Tasks)

**Check:** No separate Tasks for documentation - docs integrated into implementation Tasks

**Penalty:** MEDIUM (3 points)

**GOOD (Integrated):**
```markdown
1. **[Task] Implement OAuth 2.0 token endpoint**
   - Definition of Done:
     - [ ] Endpoint accepts grant_type parameter
     - [ ] **API docs updated in docs/api/authentication.md**
```

**BAD (Separate Doc Tasks):**
```markdown
1. [Task] Implement OAuth endpoint
2. [Task] Write API documentation  <- Separate doc task
```

**Auto-fix actions:**
1. Identify standalone doc Tasks (keywords: "Write docs", "Update README", "Document API")
2. IF found -> Remove and add doc requirement to related Task's Definition of Done
3. Update Linear issue

**Rationale:** Documentation should be created WITH implementation, not after.

---

## Criterion #9: Story Size (3-8 Tasks)

**Check:** Story has 3-8 implementation Tasks (optimal decomposition)

**Penalty:** MEDIUM (3 points)

**Optimal Task Count:**

| Complexity | Task Count | Example |
|------------|------------|---------|
| Simple | 3-4 | Add single endpoint with validation |
| Medium | 5-6 | Integrate external service (OAuth, Stripe) |
| Complex | 7-8 | Implement multi-step workflow |

**Auto-fix actions:**
1. Count implementation Tasks (exclude final test Task)
2. IF <3 Tasks -> Add warning: "Story may need splitting"
3. IF >8 Tasks -> Consolidate related Tasks
4. Update Linear issue

---

## Criterion #10: Test Cleanup (No Premature Test Tasks)

**Check:** No separate test Tasks BEFORE final Task (testing handled separately)

**Penalty:** MEDIUM (3 points)

**GOOD:**
```markdown
1. [Task] Implement login endpoint
2. [Task] Add token validation
3. [Task] Comprehensive test suite (created by test planner)
```

**BAD:**
```markdown
1. [Task] Implement login endpoint
2. [Task] Write unit tests for login  <- Premature
3. [Task] Add token validation
```

**Auto-fix actions:**
1. Find test Tasks before final Task (keywords: "test", "spec", "e2e")
2. IF found -> Remove and add testing note to related Task's DoD
3. Update Linear issue

---

## Criterion #11: YAGNI (You Aren't Gonna Need It)

**Check:** Story scope limited to current requirements (no speculative features)

**Penalty:** MEDIUM (3 points)

**CRITICAL:** YAGNI applies UNLESS Industry Standards (#5) require it. Standards override YAGNI.

**YAGNI Hierarchy:**
```
Level 1: Industry Standards (RFC, OWASP) -> CANNOT remove
Level 2: Security Standards -> CANNOT remove
Level 3: YAGNI -> Apply ONLY if no conflict with Level 1-2
```

**GOOD (Standards Override YAGNI):**
- OAuth includes refresh tokens (RFC 6749 requires, even if "not needed yet")
- Error handling includes all HTTP codes (RFC 7231 defines them)

**GOOD (YAGNI Applies):**
- Login does NOT include social auth if not required now
- API does NOT include GraphQL if REST sufficient

**BAD (Violates Standards):**
- "Skip refresh tokens for simplicity" (violates RFC 6749)

**Auto-fix actions:**
1. Identify speculative features (keywords: "future-proof", "might need", "prepare for")
2. Check if feature required by Standard:
   - IF YES -> Keep feature, add justification
   - IF NO -> Remove feature, add TODO comment
3. Update Linear issue

---

## Criterion #12: KISS (Keep It Simple, Stupid)

**Check:** Solution uses simplest approach that meets requirements

**Penalty:** MEDIUM (3 points)

**CRITICAL:** KISS applies UNLESS Industry Standards (#5) require complexity. Standards override KISS.

**KISS Hierarchy:**
```
Level 1: Industry Standards -> CANNOT simplify
Level 2: Security Standards -> CANNOT simplify
Level 3: KISS -> Apply ONLY if no conflict with Level 1-2
```

**GOOD (Standards Override KISS):**
- OAuth 2.0 with all required parameters (RFC 6749 requires)
- Helmet.js with security headers (OWASP requires)

**GOOD (KISS Applies):**
- Monolith instead of microservices (for small apps)
- SQLite instead of PostgreSQL (for dev/small apps)

**BAD (Over-engineered):**
- "Microservices for 3-endpoint API" (no scale requirement)
- "Kubernetes for single server" (Docker Compose sufficient)

**Auto-fix actions:**
1. Identify over-engineered solutions (keywords: "microservice", "kubernetes", "distributed")
2. Check if complexity justified by Standard:
   - IF YES -> Keep, add justification
   - IF NO -> Simplify, suggest alternative
3. Update Linear issue

---

## Criterion #13: Foundation-First Task Order

**Check:** Tasks ordered bottom-up (Database -> Service -> API -> UI)

**Penalty:** MEDIUM (3 points)

**Correct Order:**
```
1. Database (schema, migrations, models)
2. Repository (data access, ORM queries)
3. Service (business logic, validation)
4. API/Routes (controllers, endpoints)
5. Middleware (auth, rate limiting)
6. UI/Frontend (if applicable)
7. Tests (final Task by test planner)
```

**GOOD (Bottom-Up):**
```markdown
1. [Task] Database schema + migrations
2. [Task] Service layer (business logic)
3. [Task] API routes (controllers)
```

**BAD (Top-Down):**
```markdown
1. [Task] API routes  <- Can't implement without service
2. [Task] Database schema  <- Should be first
```

**Auto-fix actions:**
1. Identify layer for each Task (keywords: "schema", "repository", "service", "route")
2. Check if ordered bottom-up
3. IF out of order -> Reorder Tasks
4. Update Linear issue

---

## Auto-Fix Hierarchy (CRITICAL)

**Order of Checks:**
```
1. Industry Standards (#5) -> CHECKED FIRST
2. Security Standards -> CHECKED SECOND
3. KISS/YAGNI (#11-#12) -> CHECKED LAST
```

**Decision Flow:**
```
Does solution violate Industry Standard?
  -> YES: Keep complex solution, add justification
  -> NO: Continue to KISS/YAGNI check

Does simplified solution compromise security?
  -> YES: Keep complex solution
  -> NO: Apply KISS/YAGNI simplification
```

| Proposed Simplification | Standard Check | Decision |
|-------------------------|----------------|----------|
| "Skip refresh tokens" | RFC 6749 requires | REJECT |
| "Use GET for mutations" | REST violates | REJECT |
| "Remove Redis caching" | No standard | ACCEPT |
| "Remove microservices" | No standard | ACCEPT |

---

## Execution Notes

**Sequential Dependency:**
- Criteria #7-#13 depend on #1-#6 being completed first
- Cannot apply YAGNI/KISS (#11-#12) until Standards verified (#5)
- Cannot check task order (#13) until Tasks exist (#9)

**Priority Enforcement:**
- Industry Standards > Security > KISS/YAGNI
- Never compromise standards for simplicity

**Linear Updates:**
- Each criterion auto-fix updates Linear issue once
- Add single comment summarizing ALL fixes in this category

---

**Version:** 3.0.0
**Last Updated:** 2025-01-07
