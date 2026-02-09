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

| Best Practice | Detection Grep | Severity if Missing |
|---------------|----------------|---------------------|
| Dead Letter Queue (DLQ) | `dlq\|dead.?letter\|failed.?queue\|on_failed\|failedJobsQueue` | HIGH |
| Exponential backoff | `backoff\|exponential\|backoffDelay\|retry_backoff` | HIGH |
| Idempotency keys | `idempoten\|dedup\|job.?id.*unique\|unique.?job` | MEDIUM |
| Job prioritization | `priority\|PRIORITY\|prioritize\|urgent` in queue config | LOW |
| Graceful shutdown | `SIGTERM\|SIGINT\|graceful.*shut\|beforeExit\|shutdown.*handler` | HIGH |
| Concurrency control | `concurrency\|maxWorkers\|worker.?limit\|limiter\|rate.?limit` | MEDIUM |
| Job timeout | `timeout\|jobTimeout\|time_limit\|TTL` in worker config | MEDIUM |
| Progress tracking | `progress\|onProgress\|job.?status\|update_state` | LOW |

### Event-Driven

| Best Practice | Detection Grep | Severity if Missing |
|---------------|----------------|---------------------|
| Event schema versioning | `version\|schema_version\|v[0-9].*event\|EventV[0-9]` | HIGH |
| Dead letter queue | `dlq\|dead.?letter\|unprocessed\|failed.?event` | HIGH |
| Correlation IDs | `correlation.?id\|trace.?id\|request.?id\|x-correlation` | MEDIUM |
| Idempotent handlers | `idempoten\|already.?processed\|dedup\|event.?id.*check` | HIGH |
| Ordering guarantees | `partition.?key\|ordering\|sequence\|ordered` | LOW |
| Schema validation | `schema.*valid\|validate.*event\|EventSchema\|zod\|pydantic` | MEDIUM |
| Replay capability | `replay\|reprocess\|re.?emit\|event.?store\|EventStore` | LOW |

### Caching

| Best Practice | Detection Grep | Severity if Missing |
|---------------|----------------|---------------------|
| Invalidation strategy | `invalidate\|evict\|delete.*cache\|bust.*cache\|on_update.*cache` | HIGH |
| Cache-aside pattern | `get.*cache.*miss.*fetch\|cache.?aside\|read.?through` | MEDIUM |
| Key naming conventions | `cache.?key\|key.?prefix\|namespace.*cache\|key.*template` | LOW |
| Stampede prevention | `lock\|mutex\|singleflight\|debounce.*cache\|cache.?lock` | MEDIUM |
| Distributed consistency | `pub.?sub.*invalidat\|broadcast.*cache\|cluster.*cache` | LOW |
| Fallback on miss | `fallback\|miss.*fetch\|cache.*miss.*return` | MEDIUM |
| Cache warming | `warm\|preload\|prefetch\|prime.*cache\|startup.*cache` | LOW |

### Resilience

| Best Practice | Detection Grep | Severity if Missing |
|---------------|----------------|---------------------|
| Circuit breaker states | `CircuitBreaker\|circuit.?breaker\|OPEN\|HALF_OPEN\|CLOSED` in resilience code | HIGH |
| Bulkhead isolation | `Bulkhead\|bulkhead\|semaphore\|concurrent.?limit\|isolation` | MEDIUM |
| Timeout per dependency | `timeout\|Timeout\|deadline\|time_limit` per external call | HIGH |
| Fallback responses | `fallback\|Fallback\|default.*response\|graceful.*degrade` | HIGH |
| Retry with jitter | `jitter\|random.*delay\|backoff.*jitter\|retry.*random` | MEDIUM |
| Health checks | `health.?check\|readiness\|liveness\|ping\|/health` | MEDIUM |
| Graceful degradation | `degrade\|feature.?flag\|circuit.*open.*return\|fallback.*default` | LOW |

### CQRS

| Best Practice | Detection Grep | Severity if Missing |
|---------------|----------------|---------------------|
| Command/Query separation | `Command\|Query\|CommandHandler\|QueryHandler` in separate dirs | HIGH |
| Eventually consistent reads | `eventual\|async.*project\|read.?model.*update` | MEDIUM |
| Projection updates | `Projection\|project\|materialize\|ReadModel.*update` | MEDIUM |
| Event-driven updates | `on.*Event\|EventHandler\|subscribe.*update` for projections | MEDIUM |
| Read model rebuild | `rebuild\|reproject\|replay.*read.?model\|migrate.*projection` | LOW |
| Separate data stores | `readDb\|writeDb\|read.*connection\|write.*connection` | LOW |

### Repository

| Best Practice | Detection Grep | Severity if Missing |
|---------------|----------------|---------------------|
| Unit of Work | `UnitOfWork\|unit.?of.?work\|commit\|SaveChanges\|flush` | HIGH |
| Specification pattern | `Specification\|specification\|criteria\|Criteria\|filter.*query` | LOW |
| Transaction management | `transaction\|Transaction\|begin\|commit\|rollback\|@Transactional` | HIGH |
| Pagination support | `paginate\|Pagination\|skip.*take\|offset.*limit\|cursor` | MEDIUM |
| Soft delete | `soft.?delete\|is_deleted\|deleted_at\|IsDeleted\|paranoid` | LOW |
| Audit logging | `audit\|created_at\|updated_at\|modified_by\|@Audit` | MEDIUM |

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
**Version:** 1.3.0
