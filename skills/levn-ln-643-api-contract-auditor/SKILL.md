---
name: ln-643-api-contract-auditor
description: "API contract audit worker (L3). Checks layer leakage in method signatures, missing DTOs, entity leakage to API, inconsistent error contracts, redundant method overloads. Returns findings with 4-score model (compliance, completeness, quality, implementation)."
allowed-tools: Read, Grep, Glob, Bash
---

# API Contract Auditor (L3 Worker)

Specialized worker auditing API contracts, method signatures at service boundaries, and DTO usage patterns.

## Purpose & Scope

- **Worker in ln-640 coordinator pipeline** - invoked by ln-640-pattern-evolution-auditor
- Audit **API contracts** at architecture level (service boundaries, layer separation)
- Check layer leakage, DTO patterns, error contract consistency
- Return structured analysis with 4 scores (compliance, completeness, quality, implementation)

## Input (from ln-640 coordinator)

```
- pattern: "API Contracts"     # Pattern name
- locations: string[]          # Service/API directories
- adr_reference: string        # Path to related ADR
- bestPractices: object        # Best practices from MCP Ref/Context7
```

## Workflow

### Phase 1: Discover Service Boundaries

```
1. Find API layer: Glob("**/api/**/*.py", "**/routes/**/*.ts", "**/controllers/**/*.ts")
2. Find service layer: Glob("**/services/**/*.py", "**/services/**/*.ts")
3. Find domain layer: Glob("**/domain/**/*.py", "**/models/**/*.py")
4. Map: which services are called by which API endpoints
```

### Phase 2: Analyze Contracts

```
FOR EACH service file:
  Extract public method signatures (name, params, return type)
  Check each audit rule
  Collect findings
```

### Phase 3: Calculate 4 Scores

**Compliance Score (0-100):**
```
IF no layer leakage (HTTP types in service): +35
IF consistent error handling pattern: +25
IF follows project naming conventions: +20
IF no entity leakage to API: +20
```

**Completeness Score (0-100):**
```
IF all service methods have typed params: +30
IF all service methods have typed returns: +30
IF DTOs defined for complex data: +20
IF error types documented/typed: +20
```

**Quality Score (0-100):**
```
IF no boolean flag params in service methods: +25
IF no methods with >5 params without DTO: +25
IF consistent naming across module: +25
IF no redundant overloads: +25
```

**Implementation Score (0-100):**
```
IF DTOs/schemas exist and are used: +30
IF type annotations present (Python) or interfaces (TS): +25
IF validation at boundaries (Pydantic, Zod, etc.): +25
IF API response DTOs separate from domain models: +20
```

### Phase 4: Calculate Overall Score

```
overall_score = average(compliance, completeness, quality, implementation) / 10
Example: (65 + 70 + 55 + 80) / 4 / 10 = 6.75
```

### Phase 5: Return Result

```json
{
  "pattern": "API Contracts",
  "overall_score": 6.75,
  "scores": {
    "compliance": 65,
    "completeness": 70,
    "quality": 55,
    "implementation": 80
  },
  "checks": [
    {"id": "layer_leakage", "name": "Layer Leakage", "status": "failed", "details": "Service accepts parsed_body: dict in 3 methods"},
    {"id": "missing_dto", "name": "Missing DTO", "status": "warning", "details": "4 params repeated in 2 methods without grouping DTO"},
    {"id": "entity_leakage", "name": "Entity Leakage", "status": "passed", "details": "All API endpoints use response DTOs"},
    {"id": "error_contracts", "name": "Error Contracts", "status": "warning", "details": "Mixed patterns: raise + return None in UserService"},
    {"id": "redundant_overloads", "name": "Redundant Overloads", "status": "passed", "details": "No redundant method pairs found"}
  ],
  "codeReferences": ["app/services/translation/", "app/api/v1/"],
  "issues": [...],
  "gaps": {...},
  "recommendations": [...]
}
```

## Audit Rules

### 1. Layer Leakage in Signatures
**What:** Service/domain method accepts HTTP-layer types (Request, parsed body dict, headers)

**Detection:**
- Grep for service/domain methods accepting `parsed_body: dict`, `request: Request`, `form_data: dict`
- Pattern: `def translate(self, parsed_body: dict)` in service layer
- Pattern: `from fastapi import Request` imported in service/domain files
- Check: service methods should accept domain-typed params, not HTTP artifacts

**Severity:**
- **HIGH:** Service method accepts raw HTTP dict (tight coupling to transport layer)
- **MEDIUM:** Service method accepts `Request` object (should receive extracted fields)

**Recommendation:** Create domain DTO (dataclass/Pydantic model) accepted by service; API layer extracts and maps

**Effort:** M (create DTO, update service signature, update callers)

### 2. Missing DTO for Grouped Parameters
**What:** >=4 related parameters always passed together across multiple methods

**Detection:**
- Find parameter groups: same 4+ params appear in >=2 method signatures
- Example: `(account_id, engine, source_lang, target_lang, ...)` repeated across methods
- Pattern: params that logically form a "context" or "request" but are passed individually

**Severity:**
- **MEDIUM:** 4-6 related params in >=2 methods (DTO recommended)
- **LOW:** 4-6 related params in single method (borderline)

**Recommendation:** Create dataclass/NamedTuple grouping related params: `TranslationContext(engine, source_lang, target_lang, ...)`

**Effort:** M (create DTO, refactor signatures, update callers)

### 3. Entity Leakage to API
**What:** ORM/domain entity returned directly from API endpoint without response DTO

**Detection:**
- API endpoint returns ORM model object directly
- Pattern: `return user` in endpoint where `user` is SQLAlchemy model
- Pattern: `return {"user": user.__dict__}` (manual serialization of ORM entity)
- Check: look for Pydantic `response_model` or explicit serialization schema

**Severity:**
- **HIGH:** ORM entity returned with all fields (exposes internal structure, password hashes, etc.)
- **MEDIUM:** ORM entity returned with manual field selection (fragile, no schema)

**Recommendation:** Create response DTO (Pydantic BaseModel) mapping only needed fields; use `response_model` in FastAPI

**Effort:** M (create response DTO, update endpoint)

### 4. Inconsistent Error Contracts
**What:** Mixed error handling patterns within same service (some raise, some return None, some return Result)

**Detection:**
- Analyze all public methods in a service class
- Check error handling: `raise Exception`, `return None`, `return {"error": ...}`, `return Result`
- Flag if >1 pattern used within same service

**Severity:**
- **MEDIUM:** Mixed patterns within service (caller must guess error handling)
- **LOW:** Inconsistency across different services (less critical if each is internally consistent)

**Recommendation:** Standardize: either raise domain exceptions (recommended for Python) or use Result type throughout

**Effort:** M (standardize error pattern across service methods)

### 5. Redundant Method Overloads
**What:** Two methods differ only in 1-2 parameters that could be optional

**Detection:**
- Find pairs: `get_user(id)` + `get_user_with_profile(id)` → could be `get_user(id, include_profile=False)`
- Find pairs: `translate(text)` + `translate_with_qe(text)` → could be `translate(text, enable_qe=False)`
- Pattern: method names with `_with_`, `_and_`, `_full` suffix duplicating base method

**Severity:**
- **LOW:** 1-2 redundant overload pairs (minor DRY violation)
- **MEDIUM:** >3 redundant overload pairs in same service (maintenance burden)

**Recommendation:** Merge into single method with optional parameters or strategy/config object

**Effort:** S-M (merge methods, update callers)

## Critical Rules

- **Architecture-level only:** Focus on service boundaries, not internal implementation
- **Read before score:** Never score without reading actual service code
- **Best practices comparison:** Use bestPractices from coordinator for framework-specific patterns
- **Code references:** Include file paths for all findings
- **One pattern only:** Analyze "API Contracts" pattern as a whole

## Definition of Done

- Service boundaries discovered (API, service, domain layers)
- Method signatures extracted and analyzed
- All 5 checks completed:
  - layer leakage, missing DTOs, entity leakage, error contracts, redundant overloads
- 4 scores calculated with justification
- Issues identified with severity, category, suggestion, effort
- Gaps documented
- Structured result returned to coordinator

## Reference Files

- Scoring rules: `../ln-640-pattern-evolution-auditor/references/scoring_rules.md`
- Common patterns: `../ln-640-pattern-evolution-auditor/references/common_patterns.md`

---
**Version:** 1.0.0
**Last Updated:** 2026-02-04
