# Pattern Scoring Rules

4-score model for evaluating architectural pattern implementations.

## Score Categories

| Score | Focus | Question Answered |
|-------|-------|-------------------|
| Compliance | Standards | "Does it follow industry standards?" |
| Completeness | Coverage | "Are all required parts implemented?" |
| Quality | Code | "Is the implementation well-written?" |
| Implementation | Reality | "Does it actually work in production?" |

## Compliance Score (0-100)

Measures adherence to industry standards and project conventions.

| Criterion | Points | Detection |
|-----------|--------|-----------|
| Follows industry standard | +30 | Grep for pattern-specific structures (see common_patterns.md Detection Keywords) |
| Has ADR documentation | +20 | `Glob("docs/adr/*{pattern}*.md")` OR `Glob("docs/architecture/*.md")` containing pattern name |
| Consistent naming conventions | +15 | `Grep("class.*{Pattern}(Service\|Handler\|Worker\|Processor)")` + file names match (`*_processor.py`, `*Handler.ts`) |
| Follows tech stack conventions | +15 | `Grep("{standard_lib}")` — e.g., Bull/BullMQ for Node.js jobs, Celery for Python |
| No anti-patterns detected | +20 | All anti-pattern checks below return 0 matches |

**Anti-pattern detection:**

| Anti-pattern | Detection Grep | Threshold |
|--------------|----------------|-----------|
| God class | File length >500 lines containing pattern keywords | Any match = -5 |
| Circular deps | `Grep("import.*{moduleA}")` in moduleB AND `Grep("import.*{moduleB}")` in moduleA | Any match = -10 |
| Mixed concerns | `Grep("httpx\|requests\|fetch")` in job/worker files | Any match = -5 |
| Hardcoded config | `Grep("localhost\|:5432\|:6379\|password.*=.*['\"]")` in pattern files | Any match = -5 |

## Completeness Score (0-100)

Measures whether all necessary components are present.

| Criterion | Points | Detection |
|-----------|--------|-----------|
| All required components present | +40 | Per-pattern component table below (each component has Grep) |
| Error handling implemented | +20 | `Grep("try\|catch\|except\|Error\|Exception\|\.catch\\(")` + `Grep("retry\|backoff\|dlq\|dead.?letter")` |
| Logging/observability | +15 | `Grep("logger\|logging\|log\\.\|structlog\|winston")` + `Grep("metrics\|prometheus\|statsd\|trace\|opentelemetry")` |
| Tests exist | +15 | `Glob("**/test*{pattern}*")` OR `Glob("**/*{pattern}*.test.*")` OR `Glob("**/*{pattern}*.spec.*")` |
| Documentation complete | +10 | `Grep("docstring\|@param\|@returns\|\\\"\\\"\\\"")` in pattern files + ADR exists |

**Required components by pattern (with detection):**

| Pattern | Component | Detection Grep | Weight |
|---------|-----------|----------------|--------|
| Job Processing | Queue | `Queue\|createQueue\|add_task\|enqueue` | 10 |
| Job Processing | Worker | `Worker\|process\|consume\|on_message` | 10 |
| Job Processing | DLQ | `dlq\|dead.?letter\|failed.?queue\|on_failed` | 10 |
| Job Processing | Retry config | `retry\|attempts\|backoff\|maxRetries` | 10 |
| Event-Driven | Publisher | `publish\|emit\|dispatch\|produce` | 10 |
| Event-Driven | Subscriber | `subscribe\|on\\(\|listen\|consume\|handler` | 10 |
| Event-Driven | Event schema | `EventSchema\|event_type\|EventType\|schema.*event` | 10 |
| Event-Driven | Event versioning | `version\|schema_version\|v[0-9]` in event files | 10 |
| Caching | Cache client | `Cache\|Redis\|createClient\|cache_client` | 10 |
| Caching | Invalidation | `invalidate\|evict\|delete.*cache\|bust.*cache` | 15 |
| Caching | TTL config | `ttl\|expire\|maxAge\|time.?to.?live` | 15 |
| Resilience | Circuit breaker | `CircuitBreaker\|circuit.?breaker\|breaker` | 10 |
| Resilience | Timeout | `timeout\|Timeout\|deadline\|time_limit` | 10 |
| Resilience | Fallback | `fallback\|Fallback\|default.*response\|graceful` | 10 |
| Resilience | Retry | `retry\|Retry\|with_retries\|retryWhen` | 10 |
| Repository | Interface | `interface.*Repository\|Protocol.*Repository\|ABC.*Repository` | 15 |
| Repository | Implementation | `class.*Repository.*implements\|class.*Repository\\(` | 15 |
| Repository | Unit of Work | `UnitOfWork\|unit.?of.?work\|commit\|transaction` | 10 |

## Quality Score (0-100)

Measures code quality and maintainability.

| Criterion | Points | Detection |
|-----------|--------|-----------|
| Code readable (short methods) | +25 | Average method length <30 lines; `Grep("def \|function \|=>")` count vs file length |
| Maintainable (low complexity) | +25 | No deep nesting: `Grep("if.*if.*if\|for.*for.*for")` returns 0 matches |
| No code smells | +20 | All smell checks below return 0 matches |
| Follows SOLID | +15 | `Grep("interface\|abstract\|Protocol\|ABC\|@inject\|Depends\\(")` present |
| Performance optimized | +15 | `Grep("async\|await\|Promise\|cache\|memoize\|lru_cache")` present |

**Code smell detection:**

| Smell | Detection Grep | Threshold |
|-------|----------------|-----------|
| TODO/FIXME markers | `Grep("TODO\|FIXME\|HACK\|XXX\|REFACTOR")` | Any = -3 per |
| Magic numbers | `Grep("[^0-9][0-9]{2,}[^0-9]")` outside config/const files | >3 = -5 |
| Long params | `Grep("def.*,.*,.*,.*,.*,")` (5+ comma-separated) | Any = -3 per |
| Deep nesting | `Grep("^\\s{16,}(if\|for\|while)")` (4+ indent levels) | Any = -5 per |
| Large files | Pattern files >300 lines | Any = -5 per |

## Implementation Score (0-100)

Measures whether the pattern actually works in production.

| Criterion | Points | Detection |
|-----------|--------|-----------|
| Code exists and compiles | +30 | `Bash("npm run build")` or `Bash("python -m py_compile {file}")` — no errors |
| Used in production paths | +25 | `Grep("from.*{module}\|import.*{module}\|require.*{module}")` outside test files, >0 matches |
| No dead/unused implementations | +15 | `Grep("export\|__all__")` in pattern files → verify each export imported elsewhere |
| Integrated with other patterns | +15 | `Grep("@inject\|Depends\\(\|container\|config\|settings\|env")` in pattern files |
| Monitored/observable | +15 | `Grep("health.?check\|readiness\|liveness\|/health\|metrics\|prometheus")` in pattern files |

## Thresholds and Actions

| Score Range | Status | Action |
|-------------|--------|--------|
| ≥80% | ✅ Good | No action needed |
| 70-79% | ⚠️ Warning | Create improvement task (LOW priority) |
| 60-69% | ❌ Below threshold | Create refactor Story (MEDIUM priority) |
| <60% | 🚨 Critical | Create refactor Story (HIGH priority) |

## Effort Estimation

| Issue Type | Typical Effort |
|------------|----------------|
| Add missing documentation | 2h |
| Add error handling | 4h |
| Add tests | 4-8h |
| Refactor for SOLID | 1-2d |
| Add DLQ/retry logic | 4-8h |
| Major architectural change | 3-5d |

## Trend Calculation

Compare current audit with previous:

```
trend = "improving" if avg_score > prev_avg_score + 5%
trend = "declining" if avg_score < prev_avg_score - 5%
trend = "stable" otherwise
```

## Architecture Health Score

Weighted average of all patterns:

```
health_score = (
  sum(pattern.compliance * 0.25 +
      pattern.completeness * 0.25 +
      pattern.quality * 0.25 +
      pattern.implementation * 0.25)
) / pattern_count
```

## Layer Compliance Scoring

Layer violations detected by ln-642 affect **Compliance** and **Quality** scores.

### Deductions from Compliance Score

| Violation | Deduction | Rationale |
|-----------|-----------|-----------|
| I/O code in domain layer | -15 points | Violates architecture principles |
| I/O code in services layer | -10 points | Should use abstractions |
| Direct framework import in domain | -10 points | Domain should be framework-agnostic |

### Deductions from Quality Score

| Issue | Deduction | Rationale |
|-------|-----------|-----------|
| HTTP call without abstraction | -10 points | Missing client layer |
| Error handling in >2 files | -5 per extra file | Duplication, should centralize |
| Pattern coverage <80% | -10 points | Inconsistent architecture |

### Layer Violation Thresholds

| Violations Count | Impact |
|------------------|--------|
| 0 | Full score maintained |
| 1-3 | Warning, create improvement tasks |
| 4-10 | Below threshold, create refactor Story |
| >10 | Critical, prioritize architectural cleanup |

## Score Conversion

For cross-audit reporting between ln-620 (X/10) and ln-640 (0-100%):

| 4-Score Average | Equivalent X/10 | Status |
|-----------------|-----------------|--------|
| 90-100% | 9-10 | ✅ Healthy |
| 70-89% | 7-8 | ⚠️ Warning |
| 50-69% | 5-6 | ❌ Below threshold |
| <50% | <5 | 🚨 Critical |

**Formula:** `x_10 = round(percent / 10)`

---
**Version:** 1.3.0
