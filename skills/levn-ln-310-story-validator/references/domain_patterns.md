# Domain Patterns Registry

Mapping Story patterns to documentation types for ln-002 delegation during ln-310 validation.

---

## Purpose

This registry defines WHEN to delegate to ln-002-best-practices-researcher and WHAT type of document to create.

**Usage in ln-310 Phase 2:**
1. Load domain_patterns.md
2. Scan Story title + Technical Notes for trigger keywords
3. IF keywords match → Delegate to ln-002 with doc_type + topic
4. Add created doc links to Story Technical Notes

---

## Pattern Registry

| Pattern | Doc Type | Topic | Trigger Keywords | Example Output |
|---------|----------|-------|------------------|----------------|
| **OAuth/OIDC** | Manual + ADR | [library] + "Auth Strategy" | auth, oauth, oidc, token, JWT, bearer | `docs/manuals/oauth2-v7.md` + `docs/adrs/NNN-auth.md` |
| **REST API** | Guide | RESTful API Patterns | endpoint, route, controller, REST, resource | `docs/guides/NN-rest-api-patterns.md` |
| **Rate Limiting** | Guide | API Rate Limiting | rate, throttle, quota, limit | `docs/guides/NN-rate-limiting.md` |
| **Error Handling** | Guide | Error Patterns (RFC 7807) | error, exception, status code, 4xx, 5xx | `docs/guides/NN-error-handling.md` |
| **Logging** | Guide | Structured Logging | log, trace, audit, winston, pino | `docs/guides/NN-logging.md` |
| **WebSocket** | Guide | WebSocket Patterns | websocket, real-time, streaming, SSE | `docs/guides/NN-websocket.md` |
| **Pagination** | Guide | Pagination Patterns | page, offset, cursor, pagination | `docs/guides/NN-pagination.md` |
| **Caching** | Manual | [library] (redis, memcached) | cache, redis, memcached, TTL | `docs/manuals/redis-N.md` |
| **Database** | Manual | [ORM/library] | database, ORM, prisma, sequelize | `docs/manuals/prisma-N.md` |
| **Validation** | Guide | Input Validation | validate, sanitize, schema, joi, zod | `docs/guides/NN-validation.md` |
| **File Upload** | Guide | File Upload & Storage | upload, multer, file, storage, s3 | `docs/guides/NN-file-upload.md` |
| **Email** | Manual | [library] (nodemailer, sendgrid) | email, mail, smtp, sendgrid | `docs/manuals/nodemailer-N.md` |

---

## Detection Logic

### 1. Keyword Matching
```
IF Story.title OR Story.context OR Story.technical_notes contains trigger_keyword:
  → Pattern detected
```

**Example:**
- Story title: "Implement OAuth 2.0 authentication"
- Keywords detected: "oauth", "authentication"
- Pattern matched: **OAuth/OIDC**
- Action: Create Manual + ADR

### 2. Multiple Patterns
```
IF multiple patterns detected:
  → Create ALL applicable docs
```

**Example:**
- Story: "Add rate limiting to REST API"
- Patterns: **REST API** + **Rate Limiting**
- Action: Create Guide for REST + Guide for Rate Limiting

### 3. Library Detection (for Manuals)
```
IF doc_type = Manual:
  → Extract library name from Technical Notes
  → Pass library name to ln-002
```

**Example:**
- Story mentions: "Using oauth2-proxy v7.6.0"
- Action: Create `docs/manuals/oauth2-proxy-v7.md`

---

## ln-002 Delegation Examples

### Example 1: OAuth Story

**Story Title:** "Implement OAuth 2.0 authentication with GitHub"

**ln-310 Detection:**
- Keywords: "oauth", "authentication"
- Pattern: **OAuth/OIDC**
- Library: `oauth2-proxy v7.6.0`

**ln-002 Delegation:**
```
Skill(skill="ln-002-best-practices-researcher",
      args="doc_type=manual topic='oauth2-proxy v7.6.0'")

Skill(skill="ln-002-best-practices-researcher",
      args="doc_type=adr topic='Authentication Strategy'")
```

**Output:**
- `docs/manuals/oauth2-proxy-v7.md`
- `docs/adrs/NNN-auth-strategy.md`

---

### Example 2: REST API with Rate Limiting

**Story Title:** "Create user management API"

**ln-310 Detection:**
- Keywords: "RESTful", "API", "endpoints", "rate", "limiting"
- Patterns: **REST API** + **Rate Limiting**

**ln-002 Delegation:**
```
Skill(skill="ln-002-best-practices-researcher",
      args="doc_type=guide topic='RESTful API Patterns'")

Skill(skill="ln-002-best-practices-researcher",
      args="doc_type=guide topic='API Rate Limiting Pattern'")
```

**Output:**
- `docs/guides/NN-rest-api-patterns.md`
- `docs/guides/NN-rate-limiting.md`

---

### Example 3: Database with Caching

**Story Title:** "Optimize database queries with Redis caching"

**ln-310 Detection:**
- Keywords: "database", "prisma", "redis", "caching"
- Patterns: **Database** + **Caching**
- Libraries: `prisma v5.8.1`, `redis v7.2`

**ln-002 Delegation:**
```
Skill(skill="ln-002-best-practices-researcher",
      args="doc_type=manual topic='Prisma v5.8.1'")

Skill(skill="ln-002-best-practices-researcher",
      args="doc_type=manual topic='Redis v7.2'")
```

**Output:**
- `docs/manuals/prisma-5.md`
- `docs/manuals/redis-7.md`

---

## Usage Guidelines

### When to Delegate

✅ **DO delegate when:**
- Pattern clearly detected (keywords match)
- Documentation does NOT already exist
- Story is in Backlog/Todo (not Done/Canceled)

❌ **DON'T delegate when:**
- Documentation already exists (just add reference)
- Story in Done/Canceled status
- Pattern ambiguous (use MCP Ref fallback instead)

### Fallback Strategy

**IF no pattern matched BUT technical aspect missing:**
- Query MCP Ref directly for standards
- Add inline references to Technical Notes
- Log in Linear comment: "No pattern matched - used MCP Ref fallback"

---

**Version:** 2.0.0
**Last Updated:** 2025-01-07
