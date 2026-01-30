# Readiness Scoring Reference

GO/NO-GO verdict and Readiness Score calculation based on BMAD validate-next-story methodology.

## GO/NO-GO Verdict

| Verdict | Meaning | Conditions |
|---------|---------|------------|
| **GO** | Story ready for execution | Penalty Points = 0, Readiness Score ≥5, Anti-Hallucination VERIFIED |
| **NO-GO** | Story requires fixes | Any of: Penalty Points >0, Score <5, FLAGGED claims |

## Readiness Score Calculation

```
Readiness Score = 10 - (Penalty Points / 5)
```

| Penalty Points | Readiness Score | Gate |
|----------------|-----------------|------|
| 0 | 10 | GO |
| 1-5 | 9 | GO |
| 6-10 | 8 | GO |
| 11-15 | 7 | GO |
| 16-20 | 6 | GO (with notes) |
| 21-25 | 5 | GO (with notes) |
| 26-30 | 4 | NO-GO |
| 31-40 | 3-2 | NO-GO |
| >40 | 1 | NO-GO (critical) |

## Anti-Hallucination Verification

### Claims to Verify

| Claim Type | Example | Verification Method |
|------------|---------|---------------------|
| RFC reference | "RFC 7231" | MCP Ref search confirms RFC exists |
| OWASP rule | "OWASP A01:2021" | MCP Ref search confirms rule |
| Library version | "Express v4.19" | Context7 query confirms version |
| Security pattern | "PKCE flow" | MCP Ref search confirms pattern |
| Performance claim | "O(log n)" | Algorithm documentation |

### Verification Process

1. Extract all technical claims from Story/Tasks
2. For each claim:
   - Query MCP Ref: `ref_search_documentation("[claim]")`
   - Query Context7: `resolve-library-id` + `query-docs`
3. Mark as:
   - **VERIFIED**: Found in MCP Ref/Context7 results
   - **UNVERIFIED**: No evidence found

### Status Determination

| Unverified Claims | Status | Action |
|-------------------|--------|--------|
| 0 | VERIFIED | Proceed |
| 1-2 | FLAGGED | List claims, suggest sources |
| >2 | FLAGGED + NO-GO | Requires correction |

## Task-AC Coverage Matrix

### Building the Matrix

1. List all Acceptance Criteria (AC1, AC2, ...)
2. For each AC, find implementing Task(s)
3. Map: AC → Task IDs
4. Calculate coverage: `covered / total`

### Coverage Thresholds

| Coverage | Status | Gate Impact |
|----------|--------|-------------|
| 100% | Full coverage | No penalty |
| 80-99% | Partial | -3 penalty points |
| <80% | Insufficient | -5 penalty points, NO-GO |

### Matrix Format

```
| AC | Description | Task(s) | Coverage |
|----|-------------|---------|----------|
| AC1 | User can login | T-001 | COVERED |
| AC2 | Error shown on failure | T-001, T-002 | COVERED |
| AC3 | Rate limiting | — | UNCOVERED |
```

## Final Assessment Output

```yaml
final_assessment:
  gate: GO | NO-GO
  readiness_score: 10
  penalty_points:
    before: 18
    after: 0
  anti_hallucination:
    status: VERIFIED
    claims_checked: 5
    unverified: []
  ac_coverage:
    covered: 5
    total: 5
    percentage: 100%
    matrix:
      - ac: "AC1"
        tasks: ["T-001"]
        status: "covered"
```

---
**Version:** 1.0.0
