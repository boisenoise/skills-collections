# Research Guidelines

<!-- SCOPE: Research quality guidelines ONLY. Contains source credibility hierarchy, citation rules, version verification, time-boxing. -->
<!-- DO NOT add here: research implementation → ln-001-standards-researcher SKILL.md, document generation → ln-002-best-practices-researcher -->

Quality guidelines for library and standards research to ensure accurate, up-to-date, and actionable information.

## Source Credibility Hierarchy

Use this priority order when selecting sources:

| Priority | Source Type | Example | When to Use |
|----------|-------------|---------|-------------|
| **1** | Official documentation | Python.org, FastAPI docs, RFC specifications | ALWAYS prefer official docs |
| **2** | Industry standards | RFC 6749 (OAuth), OpenAPI 3.0 spec, OWASP guidelines | For protocol/standard compliance |
| **3** | Vendor documentation | AWS docs, Redis docs, PostgreSQL docs | For specific vendor implementations |
| **4** | Community standards | PEP (Python), JSR (Java), WCAG (accessibility) | For language/platform best practices |
| **5** | Authoritative blogs | Real Python, DigitalOcean tutorials, vendor blogs | For complex integration examples |
| **6** | Stack Overflow | Accepted answers with high votes (500+) | LAST RESORT - verify info elsewhere |

**RED FLAGS (avoid):**
- Blog posts > 2 years old (outdated patterns)
- Personal blogs without credentials
- Medium posts without verification
- Reddit/forum posts (use for direction only)

---

## Version Selection Guidelines

| Scenario | Preferred Version | Rationale |
|----------|-------------------|-----------|
| **Production projects** | Latest LTS (Long Term Support) | Stability + security updates |
| **New features** | Latest stable release | Modern APIs, avoid beta/RC |
| **Legacy projects** | Match existing version (upgrade path in separate Story) | Avoid breaking changes |
| **Experimental** | Latest (including RC) | ONLY if Epic explicitly requests bleeding edge |

**Version notation:**
- ✅ GOOD: "v3.12.1 (LTS)" or "v2.5.0 (stable)"
- ❌ BAD: "latest" or "v3.x" (not specific)

**Deprecation check:**
- If library has deprecated methods → List in "Key constraints"
- If library is end-of-life → Suggest alternatives

---

## Key APIs Extraction

**Focus on 2-5 MOST RELEVANT methods for Story domain:**

### Good Example (rate limiting Story):
```
**Key APIs:**
- `Limiter(key_func=get_remote_address, default_limits=["200/day"])` - Initialize rate limiter with default limits
- `@limiter.limit("5/minute")` - Decorator for route-specific limits
- `limiter.reset()` - Reset limits programmatically (testing, admin operations)
```

### Bad Example (too generic):
```
**Key APIs:**
- Constructor
- Methods
- Properties
```

**Extraction rules:**
1. Include method signature (parameters, return type if critical)
2. Explain WHEN to use (not just WHAT it does)
3. Prioritize methods for Story domain (not all library methods)
4. If >5 methods → group by category (CRUD, validation, utilities)

---

## Constraints and Limitations

**MUST document:**
- Async/sync support (e.g., "slowapi v0.1.9 has NO async support")
- Storage backends (e.g., "in-memory storage doesn't persist across restarts")
- Multi-process caveats (e.g., "Limiter doesn't share state across workers without Redis")
- Platform limitations (e.g., "Windows async I/O has known issues")
- Performance limitations (e.g., "max 10K requests/sec without Redis backend")

**Format:**
```markdown
**Key constraints:**
- [Limitation]: [Brief explanation] - [Workaround or solution]
```

**Example:**
```markdown
**Key constraints:**
- No async support in v0.1.9 - Use slowapi v0.2.0+ OR sync endpoints only
- In-memory storage loses data on restart - Use Redis backend for production
- Rate limiting doesn't work across multiple workers - Configure Redis shared storage
```

---

## Standards Compliance

**Industry standards to check (by domain):**

| Domain | Relevant Standards |
|--------|-------------------|
| **Authentication** | OAuth 2.0 (RFC 6749), OpenID Connect, JWT (RFC 7519) |
| **REST API** | OpenAPI 3.0, REST principles (RFC 7231), HATEOAS |
| **Security** | OWASP Top 10, NIST guidelines, CSP (Content Security Policy) |
| **Data formats** | JSON Schema, Protocol Buffers, Avro |
| **Protocols** | HTTP/2 (RFC 7540), WebSocket (RFC 6455), gRPC |
| **Accessibility** | WCAG 2.1, ARIA, Section 508 |

**Format:**
```markdown
**Standards compliance:**
- [Standard/RFC name]: [How Story should comply - brief description]
```

**Example:**
```markdown
**Standards compliance:**
- RFC 6749 (OAuth 2.0): Use authorization code flow with PKCE for web apps
- OWASP Top 10 (2021): Implement rate limiting to prevent brute-force attacks (A07:2021)
- OpenAPI 3.0: Document rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
```

---

## Research Summary Template

```markdown
## Library Research
**Primary libraries:**
| Library | Version | Purpose | Docs |
|---------|---------|---------|------|
| slowapi | v0.2.1 (stable) | Rate limiting for FastAPI endpoints | [GitHub](https://github.com/laurentS/slowapi) |
| redis-py | v5.0.0 (stable) | Redis backend for distributed rate limiting | [Redis docs](https://redis.io/docs/clients/python/) |

**Key APIs:**
- `Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")` - Initialize with Redis backend for multi-worker support
- `@limiter.limit("5/minute")` - Apply per-route rate limits (returns 429 on exceed)
- `@limiter.exempt` - Exempt specific routes (admin endpoints, health checks)

**Key constraints:**
- slowapi v0.1.9 has NO async support - Upgrade to v0.2.0+ for FastAPI async routes
- In-memory storage loses data on restart - Use Redis backend for production environments
- Rate limiting doesn't work across multiple workers without shared storage - Configure Redis URI

**Standards compliance:**
- RFC 6585 (HTTP 429): Return 429 Too Many Requests with Retry-After header
- OWASP A07:2021 (Identification/Auth Failures): Implement rate limiting on login endpoints (5 attempts/15 min)
- OpenAPI 3.0: Document rate limit response headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)

**Existing guides:**
- [docs/guides/rate_limiting_pattern.md](docs/guides/rate_limiting_pattern.md) - Rate limiting best practices for FastAPI
```

---

## Time Management

**Time-box: 15-20 minutes maximum per Epic**

**Time allocation:**
- Phase 1 (Identify): 2-3 minutes
- Phase 2 (Context7): 5-7 minutes (parallel calls)
- Phase 3 (Ref): 5-7 minutes (parallel calls)
- Phase 4 (Guides): 1-2 minutes
- Phase 5 (Summary): 2-3 minutes

**If time exceeds:**
- Reduce library count (focus on 2-3 primary libraries)
- Skip fallback WebSearch
- Use cached Ref results from previous Epics

---

## Quality Checklist

Before returning Research Summary, verify:

- [ ] All libraries have specific versions (not "latest")
- [ ] Key APIs (2-5 methods) include when to use (not just what)
- [ ] Constraints list workarounds or solutions
- [ ] Standards compliance includes HOW to comply (not just standard name)
- [ ] Official docs URLs are valid (not broken links)
- [ ] Research Summary is ≤ 500 words (concise, actionable)

---

**Version:** 1.0.0
**Last Updated:** 2025-11-17
