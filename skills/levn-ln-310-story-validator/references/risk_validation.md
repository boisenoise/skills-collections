# Risk Validation (Criterion #20)

<!-- SCOPE: Implementation risk analysis criterion #20 ONLY. Contains risk categories, Impact x Probability scoring, auto-fix rules. -->
<!-- DO NOT add here: Testing risks -> risk_based_testing_guide.md, dependencies -> dependency_validation.md, security standards -> standards_validation.md -->

Detailed rules for implementation risk analysis in Story/Tasks.

---

## Criterion #20: Risk Analysis

**Check:** Story/Tasks identify and mitigate implementation risks with Priority >= 9

**Penalty:** HIGH (5 points) per unmitigated risk with Priority >= 15; MEDIUM (3 points) for Priority 9-14

**Cap:** Max 15 points (3 violations maximum counted)

**Uses:** Impact x Probability matrix from `shared/references/risk_based_testing_guide.md`

---

## Risk Categories

### R1: Architectural Decisions Without Justification

**Check:** Non-trivial architectural choices (patterns, infrastructure, data flow) have documented rationale or ADR reference

**Keywords:** architecture, pattern, CQRS, saga, event-driven, microservice, monolith, event sourcing, message queue

**GOOD:**
```markdown
## Technical Notes
Architecture: Event-driven with RabbitMQ for order processing.
Rationale: Decouples payment from fulfillment (ADR-003). Fallback: sync processing if queue unavailable.
```

**BAD:**
```markdown
## Technical Notes
Architecture: Event-driven with RabbitMQ for order processing.
```
No rationale, no ADR reference, no fallback strategy.

**Auto-fix:** FLAG only (architectural decisions require human judgment)
- Add comment: "Architectural decision [X] detected without rationale. Consider creating ADR via ln-002."

---

### R2: Missing Error Handling Strategy

**Check:** External calls and multi-step operations have explicit error handling (retry, fallback, timeout, circuit breaker)

**Keywords:** error, exception, retry, fallback, timeout, circuit breaker, dead letter, compensation

**GOOD:**
```markdown
## Implementation Plan
Call Stripe API with:
- Timeout: 10s per request
- Retry: 3x exponential backoff (1s, 2s, 4s)
- Fallback: Queue payment for manual processing
- Circuit breaker: Open after 5 consecutive failures
```

**BAD:**
```markdown
## Implementation Plan
Call Stripe API to process payment.
Create order record after successful payment.
```
No timeout, no retry, no fallback for external API failure.

**Auto-fix:** Add `_TODO: Define error handling for [detected integration/operation]: timeout, retry policy, fallback strategy_` to Task Implementation Plan.

---

### R3: Scalability Concerns

**Check:** Data operations have bounds (pagination, limits, batch sizes); no unbounded queries or O(n^2) patterns

**Keywords:** scale, concurrent, batch, pagination, limit, all records, full scan, load all, fetch all, no limit

**GOOD:**
```markdown
## Technical Approach
Fetch users with cursor-based pagination (limit 50 per page).
Batch email sending: 100 per batch with 1s delay between batches.
```

**BAD:**
```markdown
## Technical Approach
Fetch all users from database.
Send notification email to each user.
```
Unbounded query + unbounded loop = O(n) memory + O(n) time with no limits.

**Auto-fix:** Add `_TODO: Define pagination/batch limits for [detected unbounded operation]_` to Task Technical Approach.

---

### R4: Data Integrity Risks

**Check:** Multi-step data operations use transactions; destructive operations have safeguards

**Keywords:** transaction, rollback, constraint, cascade, delete, drop, truncate, migrate, atomic, consistency

**GOOD:**
```markdown
## Implementation Plan
1. Begin transaction
2. Create order record
3. Deduct inventory
4. Charge payment
5. Commit (or rollback all on failure)

Migration: Add column with default value (non-breaking). Backfill in batches.
```

**BAD:**
```markdown
## Implementation Plan
1. Create order record
2. Deduct inventory
3. Charge payment
```
No transaction wrapping. If step 3 fails, inventory already deducted = data inconsistency.

**Auto-fix:** Add `_TODO: Wrap [multi-step operation] in transaction with rollback on failure_` to Task Implementation Plan.

---

### R5: Integration Risks with External Systems

**Check:** External API/service integrations define SLA expectations, timeout, retry, and dev mock strategy

**Keywords:** API, external, third-party, webhook, integration, service, provider, vendor, OAuth, SSO

**GOOD:**
```markdown
## Technical Approach
Stripe integration:
- Expected SLA: 99.9%, avg response 200ms
- Timeout: 10s, Retry: 3x with backoff
- Dev environment: Use Stripe test mode (no mocks needed)
- Webhook: Idempotent processing with event ID dedup
```

**BAD:**
```markdown
## Technical Approach
Integrate with Stripe for payment processing.
Listen for Stripe webhooks.
```
No SLA, no timeout, no retry, no idempotency for webhooks.

**Auto-fix:** Add `### Integration Points` section with `_TODO: Define timeout/retry/fallback for [external service]. Define webhook idempotency strategy._`

---

### R6: Single Points of Failure

**Check:** Critical-path components have degradation strategy or redundancy plan

**Keywords:** single, central, only one, depends entirely, critical path, no alternative, sole provider

**GOOD:**
```markdown
## Technical Notes
Auth: Primary IdP = Auth0. Fallback: cached JWT validation (grace period 1h if IdP unavailable).
Database: Primary PostgreSQL with read replica. Failover: automatic via connection pool.
```

**BAD:**
```markdown
## Technical Notes
Auth: Auth0 for all authentication.
Database: PostgreSQL.
```
No fallback for IdP outage. No mention of replication/failover.

**Auto-fix:** FLAG only (redundancy decisions require cost/architecture trade-offs)
- Add comment: "Single point of failure detected: [component]. Consider graceful degradation strategy."

---

## Scoring Algorithm

```
FOR EACH risk category R1-R6:
  1. SCAN Story (Technical Notes, Dependencies) + Tasks (Implementation Plan, Technical Approach)
  2. DETECT risk indicators via keywords
  3. IF risk indicator found:
     a. CHECK if mitigation documented (retry, fallback, transaction, ADR ref, timeout, degradation)
     b. IF mitigated -> PASS (0 points)
     c. IF NOT mitigated:
        - Assign Impact (1-5) and Probability (1-5) per risk_based_testing_guide.md
        - Calculate Priority = Impact x Probability
        - IF Priority >= 15 -> HIGH (5 points)
        - IF Priority 9-14  -> MEDIUM (3 points)
        - IF Priority <= 8   -> SKIP (0 points)
  4. IF NO risk indicators for category -> PASS (0 points)

TOTAL = sum of all penalties (cap at 15 points)
```

**Default Impact x Probability by category:**

| Category | Default Impact | Default Probability | Default Priority | Notes |
|----------|---------------|--------------------|--------------------|-------|
| R1: Architectural Decisions | 4 | 3 | 12 (MEDIUM) | Raise to 5x4=20 if system-wide pattern |
| R2: Error Handling | 4 | 4 | 16 (HIGH) | External calls almost always need handling |
| R3: Scalability | 3 | 3 | 9 (MEDIUM) | Raise if user-facing or data-heavy |
| R4: Data Integrity | 5 | 4 | 20 (HIGH) | Data loss = highest business impact |
| R5: Integration | 4 | 4 | 16 (HIGH) | External systems are inherently unreliable |
| R6: SPOF | 5 | 2 | 10 (MEDIUM) | Low probability but catastrophic impact |

Override defaults when Story context indicates higher/lower risk (e.g., internal tool vs public API).

---

## Auto-fix vs Human Review

| Priority Range | Action | Rationale |
|----------------|--------|-----------|
| >= 20 | FLAG only (human review mandatory) | Too high-impact for automated TODO |
| 15-19 | Add TODO placeholder + FLAG | Actionable but needs human verification |
| 9-14 | Add TODO placeholder (silent) | Important but lower urgency |
| <= 8 | SKIP | Risk too low to warrant Story-level documentation |

**Auto-fixable categories:** R2 (TODO for error handling), R3 (TODO for limits), R4 (TODO for transactions), R5 (TODO for integration points)

**Human review only:** R1 (architectural decisions), R6 (SPOF at design level), any risk with Priority >= 20

---

## Skip Fix When

- Story has explicit "Risk Assessment" or "Risks and Mitigations" section with documented risks
- Story/Task in Done/Canceled status
- Story scope is trivial (1-2 Tasks, no external dependencies, no DB changes, no architectural decisions)
- All detected risks already have mitigation documented in Technical Notes

---

## Execution Order

**Group 7 (NEW): Risk (#20) runs after Dependencies, before Traceability**

**Rationale:**
- Needs structural fixes complete (#1-#4) to find Technical Notes sections
- Needs standards applied (#5) to distinguish standard-required complexity from risk
- Needs dependencies resolved (#18-#19) to avoid flagging already-fixed issues
- Must run before Traceability (#16-#17) since risk TODOs may affect AC-Task mapping

**Sequence:**
```
Phase 4 Groups 1-6 complete:
  - Structural (#1-#4)
  - Standards (#5)
  - Solution (#6)
  - Workflow (#7-#13)
  - Quality (#14-#15)
  - Dependencies (#18-#19)

-> Group 7: Risk (#20) runs
  - Scan for risk indicators
  - Score via Impact x Probability
  - Auto-fix or FLAG

-> Group 8: Traceability (#16-#17) runs
  - Verify final alignment and coverage
```

---

## Integration with Other Criteria

**Criterion #5 (Standards Compliance):**
- #5 checks RFC/OWASP references exist
- #20 checks risk mitigation strategies exist
- Overlap: security risks detected by #20 may already be covered by #5 OWASP checks
- Rule: If #5 already flagged an issue with OWASP reference, #20 does NOT double-count

**Criterion #15 (Code Quality Basics):**
- #15 checks hardcoded values
- #20.R5 checks external integrations
- Rule: Hardcoded API keys found by #15 are NOT re-flagged by #20.R5

**ln-311 risk_analysis area:**
- #20 enforces "did you document risks?" (structural/compliance check)
- ln-311 risk_analysis asks "what risks did agents find independently?" (analytical review)
- Complementary: #20 runs in Phase 4, ln-311 in Phase 5

---

**Version:** 1.0.0
**Last Updated:** 2026-02-11
