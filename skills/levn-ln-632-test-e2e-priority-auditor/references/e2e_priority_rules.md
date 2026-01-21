# E2E Priority Audit Rules

<!-- SCOPE: E2E test baseline requirements ONLY. Contains 2-test-per-endpoint rule, endpoint discovery patterns. -->
<!-- DO NOT add here: Audit workflow → ln-632-test-e2e-priority-auditor SKILL.md -->

E2E baseline requirements and test pyramid validation.

## E2E Baseline Rule

**Every HTTP endpoint MUST have 2 E2E tests:**

1. **Positive scenario** (happy path, 200 OK)
2. **Negative scenario** (error handling, 4xx/5xx)

### Endpoint Discovery

**Patterns to find endpoints:**
- Express: `app.get()`, `app.post()`, `router.put()`, etc.
- Fastify: `fastify.get()`, `server.post()`, etc.
- Next.js API routes: `export default function handler()` in `pages/api/`

**Example:**
```javascript
// routes/users.ts
app.get('/users/:id', getUserById);
app.post('/users', createUser);
app.delete('/users/:id', deleteUser);

// Required E2E tests (6 total):
// 1. GET /users/:id (200 OK)
// 2. GET /users/:id (404 Not Found)
// 3. POST /users (201 Created)
// 4. POST /users (400 Bad Request - invalid data)
// 5. DELETE /users/:id (204 No Content)
// 6. DELETE /users/:id (404 Not Found)
```

## When Unit/Integration Justified

| Scenario | Justification | Example |
|----------|---------------|---------|
| **Algorithm branches** | E2E can't easily cover all branches | Tax calculation with 50 country rules → Unit test edge cases |
| **Performance** | E2E >5s per test | Concurrency test with 100 parallel requests → Unit test |
| **Complex errors** | Hard to trigger via E2E | Network timeout, DB deadlock → Integration test with mocks |
| **Edge cases** | Exhaustive testing impractical | Date parsing with 100 format variations → Unit test |

**Rule:** If Unit test is NOT justified → convert to E2E or delete.

## Test Pyramid Targets

| Test Type | Percentage | Role |
|-----------|------------|------|
| **E2E** | 30-40% | **Primary** — prove feature works end-to-end |
| **Integration** | 20-30% | **Supplementary** — complex module interactions |
| **Unit** | 30-50% | **Supplementary** — fast feedback, algorithm testing |

### Red Flags

| Anti-Pattern | Indicator | Fix |
|--------------|-----------|-----|
| **Inverted Pyramid** | 70% Unit, 10% E2E | Add E2E for main flows, remove trivial Unit tests |
| **No E2E** | 0% E2E, 100% Unit | Add E2E baseline for all endpoints |
| **E2E Overload** | 90% E2E, slow test suite (>10 min) | Convert some E2E to Integration (mock DB/APIs) |

## Good vs Bad Examples

### Example 1: Missing E2E (BAD)

```javascript
// Endpoint exists
app.post('/payment', processPayment);

// Only Unit test (BAD)
test('processPayment calculates total', () => {
  const result = processPayment({ amount: 100, discount: 0.2 });
  expect(result.total).toBe(80);
});
```

**Issue:** No E2E test — can't prove endpoint works (routing, serialization, DB, etc.)

**Fix:** Add E2E test:
```javascript
test('POST /payment returns 200 with receipt', async () => {
  const response = await request(app)
    .post('/payment')
    .send({ amount: 100, discount: 0.2 });

  expect(response.status).toBe(200);
  expect(response.body.total).toBe(80);
  expect(response.body.receiptId).toBeDefined();
});
```

### Example 2: Missing Negative E2E (BAD)

```javascript
// Only positive E2E (BAD)
test('GET /users/:id returns user', async () => {
  const response = await request(app).get('/users/123');
  expect(response.status).toBe(200);
});
```

**Issue:** No negative scenario — what if user doesn't exist?

**Fix:** Add negative E2E:
```javascript
test('GET /users/:id returns 404 for nonexistent user', async () => {
  const response = await request(app).get('/users/999999');
  expect(response.status).toBe(404);
  expect(response.body.error).toBe('User not found');
});
```

### Example 3: Justified Unit Test (GOOD)

```javascript
// Complex tax calculation
function calculateTax(amount: number, country: string): number {
  // 50 country-specific rules...
}

// E2E test (baseline)
test('POST /checkout calculates tax correctly', async () => {
  const response = await request(app)
    .post('/checkout')
    .send({ amount: 100, country: 'US' });

  expect(response.body.tax).toBe(7.5); // US tax rate
});

// Unit tests for edge cases (JUSTIFIED)
test('calculateTax handles all 50 countries', () => {
  expect(calculateTax(100, 'US')).toBe(7.5);
  expect(calculateTax(100, 'UK')).toBe(20);
  expect(calculateTax(100, 'JP')).toBe(10);
  // ... 47 more
});
```

**Justification:** E2E covers happy path, Unit tests cover exhaustive country rules.

## Critical Endpoints (MUST have E2E)

| Category | Endpoints | Example |
|----------|-----------|---------|
| **Auth** | `/login`, `/logout`, `/register`, `/refresh-token` | `POST /login` → 200 (success) + 401 (invalid credentials) |
| **Money** | `/payment`, `/checkout`, `/refund`, `/invoice` | `POST /payment` → 200 (success) + 400 (insufficient funds) |
| **Core CRUD** | `/users`, `/products`, `/orders` | `GET /users/:id` → 200 (found) + 404 (not found) |

**Severity:** **CRITICAL** if missing E2E for these endpoints.

---
**Version:** 1.0.0
**Last Updated:** 2025-12-21
