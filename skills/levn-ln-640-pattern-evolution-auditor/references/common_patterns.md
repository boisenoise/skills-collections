# Common Architectural Patterns

Detection patterns and best practices reference for ln-640/ln-641.

## Pattern Detection (Grep)

| Pattern | Detection Keywords | File Types |
|---------|-------------------|------------|
| Job Processing | `Queue\|Worker\|Job\|Bull\|BullMQ\|Celery\|Sidekiq` | *.ts, *.js, *.py, *.rb |
| Event-Driven | `EventEmitter\|publish\|subscribe\|emit\|on\(\s*['"]` | *.ts, *.js, *.py |
| Caching | `Cache\|Redis\|Memcached\|TTL\|invalidate\|@Cacheable` | *.ts, *.js, *.py, *.java |
| Resilience | `CircuitBreaker\|Retry\|Timeout\|Fallback\|Bulkhead` | *.ts, *.js, *.py |
| CQRS | `Command\|Query\|ReadModel\|WriteModel\|CommandHandler` | *.ts, *.js, *.cs |
| Saga | `Saga\|Orchestrator\|Compensate\|SagaStep` | *.ts, *.js, *.py |
| Repository | `Repository\|findBy\|findOne\|save\|delete\|@Repository` | *.ts, *.js, *.py, *.java |
| API Gateway | `Gateway\|Proxy\|RateLimit\|ApiGateway` | *.ts, *.js, *.py |
| Event Sourcing | `EventStore\|Aggregate\|AggregateRoot\|DomainEvent` | *.ts, *.js, *.cs |
| Message Queue | `RabbitMQ\|Kafka\|SQS\|AMQP\|MessageBroker` | *.ts, *.js, *.py |

## Key Best Practices by Pattern

### Job Processing
- Dead Letter Queue (DLQ) for failed jobs
- Exponential backoff for retries
- Idempotency keys for duplicate prevention
- Job prioritization and scheduling
- Graceful shutdown handling
- Concurrency control (per worker limits)
- Job timeout configuration
- Progress tracking and logging

### Event-Driven
- Event schema versioning
- Dead letter queue for unprocessed events
- Event correlation IDs for tracing
- Idempotent event handlers
- Event ordering guarantees (when needed)
- Schema registry for validation
- Replay capability

### Caching
- Cache invalidation strategy (TTL, event-based)
- Cache-aside pattern implementation
- Cache key naming conventions
- Cache stampede prevention
- Distributed cache consistency
- Fallback to source on cache miss
- Cache warming strategies

### Resilience
- Circuit breaker with states (closed, open, half-open)
- Bulkhead isolation
- Timeout configuration per dependency
- Fallback responses
- Retry with jitter
- Health checks for dependencies
- Graceful degradation

### CQRS
- Command/Query separation
- Eventually consistent read models
- Projection update strategies
- Event-driven updates
- Read model rebuild capability
- Separate data stores (optional)

### Repository
- Unit of Work pattern
- Specification pattern for complex queries
- Transaction management
- Pagination support
- Soft delete handling
- Audit logging

## MCP Ref Search Queries

Use these queries with `ref_search_documentation`:

| Pattern | Search Query |
|---------|-------------|
| Job Processing | "job queue best practices {tech_stack} dead letter retry" |
| Event-Driven | "event driven architecture patterns {tech_stack} event sourcing" |
| Caching | "caching strategies {tech_stack} cache invalidation redis" |
| Resilience | "circuit breaker pattern {tech_stack} retry timeout" |
| CQRS | "cqrs pattern {tech_stack} command query separation" |
| Repository | "repository pattern {tech_stack} unit of work" |

## Context7 Libraries

| Pattern | Library to Query |
|---------|-----------------|
| Job Processing (Node.js) | bull, bullmq |
| Job Processing (Python) | celery |
| Event-Driven (Node.js) | eventemitter2, rxjs |
| Caching (Node.js) | ioredis, node-cache |
| Resilience (Node.js) | cockatiel, opossum |
| CQRS (.NET) | mediatr |

## Layer Violation Detection

Used by ln-642-layer-boundary-auditor to detect architectural violations.

### Auto-Discovery from docs/architecture.md

Read Section 4.2 (Top-Level Decomposition) and Section 5.3 (Infrastructure Layer Components) to determine project's layer structure and allowed dependencies.

### Common Architecture Presets (fallback if no architecture.md)

| Architecture | Layers | Dependency Direction |
|--------------|--------|---------------------|
| Layered (n-tier) | Presentation → Business → Data | top-down only |
| Hexagonal | Ports ↔ Adapters ← Domain | adapters depend on ports |
| Clean | Controllers → UseCases → Entities | outside-in |
| Vertical Slices | Feature modules | no cross-slice deps |
| MVC | View → Controller → Model | no Model→View |

### I/O Pattern Boundary Rules

Regardless of architecture, these patterns should be isolated in infrastructure/adapters:

| Pattern | Forbidden In | Detection Grep | Allowed In |
|---------|--------------|----------------|------------|
| HTTP Client | domain/, services/, api/ | `httpx\\.\|aiohttp\\.\|requests\\.(get\|post)` | infrastructure/http/, clients/ |
| DB Session | domain/, services/, api/ | `session\\.(execute\|query\|add\|commit)` | infrastructure/persistence/, repositories/ |
| Raw SQL | domain/, services/ | `SELECT\\s.*FROM\|INSERT\\s+INTO` | infrastructure/persistence/ |
| File I/O | domain/ | `open\\(\|Path\\(.*\\)\\.(read\|write)` | infrastructure/storage/ |
| Env Access | domain/ | `os\\.(environ\|getenv)` | core/config/, settings/ |
| Framework | domain/ | `from\\s+(fastapi\|flask\|django)` | api/, infrastructure/ |

### Coverage Checks

| Check | Grep Pattern | Threshold |
|-------|--------------|-----------|
| HTTP Abstraction | `client\\.(get\|post\|put\|delete)` vs direct calls | 90% |
| Error Centralization | `except\\s+(httpx\|aiohttp\|requests)\\.` in ≤2 files | Yes |

## Cross-Layer Consistency Checks

Used by ln-642 Phase 2.5 to detect patterns that span multiple layers inconsistently.

### Transaction Boundary Rules

| Owner Layer | commit() Allowed In | commit() Forbidden In |
|-------------|---------------------|----------------------|
| Service-owned UoW | services/ | repositories/, api/ |
| Endpoint-owned UoW | api/ | repositories/, services/ |
| Repository-owned UoW | repositories/ | services/, api/ |

**Detection:**
```
repo_commits = Grep("\\.commit\\(\\)\|\\.rollback\\(\\)", "**/repositories/**")
service_commits = Grep("\\.commit\\(\\)\|\\.rollback\\(\\)", "**/services/**")
api_commits = Grep("\\.commit\\(\\)\|\\.rollback\\(\\)", "**/api/**")
```

**Safe Patterns (not violations):**
- `# best-effort telemetry` comment in context
- `_callbacks.py` files (progress notifiers)
- `# UoW boundary` explicit marker

### Session Ownership Rules

| Pattern | Detection | Severity |
|---------|-----------|----------|
| DI + Local mix | `Depends(get_session)` in API AND `AsyncSessionLocal()` in service/repo | HIGH |
| Service local session | `AsyncSessionLocal()` in service calling DI-based repo | MEDIUM |

### Async Consistency Rules

| Blocking Pattern | Detection in `async def` | Safe Alternative |
|------------------|-------------------------|------------------|
| File read | `\\.read_bytes\\(\\)\|\\.read_text\\(\\)` | `asyncio.to_thread()` |
| File write | `\\.write_bytes\\(\\)\|\\.write_text\\(\\)` | `asyncio.to_thread()` |
| open() | `(?<!aiofiles\\.)open\\(` | `aiofiles.open()` |
| time.sleep | `time\\.sleep\\(` | `asyncio.sleep()` |
| requests | `requests\\.(get\|post)` | `httpx.AsyncClient` |

### Fire-and-Forget Rules

| Pattern | Detection | Severity |
|---------|-----------|----------|
| Task without handler | `create_task\\(` without `.add_done_callback(` | MEDIUM |
| Task in loop | `for.*create_task\\(` without error collection | HIGH |

**Safe Patterns:**
- `# fire-and-forget` comment documenting intent
- Task assigned to variable with later `await`
- Explicit `.add_done_callback(handle_exception)`

---
**Version:** 1.2.0
