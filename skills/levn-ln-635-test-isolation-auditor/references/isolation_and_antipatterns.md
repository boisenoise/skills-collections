# Test Isolation & Anti-Patterns Catalog

<!-- SCOPE: Test isolation checklist and anti-patterns ONLY. Contains 6 isolation categories, determinism rules, flaky test patterns. -->
<!-- DO NOT add here: Audit workflow → ln-635-test-isolation-auditor SKILL.md -->

Isolation checklist, determinism rules, and anti-pattern detection.

## Isolation Checklist (6 Categories)

### 1. External APIs

| Good | Bad | Detection | Fix |
|------|-----|-----------|-----|
| Mocked (`nock`, `jest.mock`, `sinon`) | Real HTTP calls | Grep for `axios.get(`, `fetch(` without mocks | Mock with `nock` or `jest.mock('axios')` |

**Example (Bad):**
```javascript
test('fetchUserData returns user', async () => {
  const user = await axios.get('https://api.github.com/users/alice'); // Real API call
  expect(user.data.login).toBe('alice');
});
```

**Example (Good):**
```javascript
test('fetchUserData returns user', async () => {
  nock('https://api.github.com').get('/users/alice').reply(200, { login: 'alice' });

  const user = await axios.get('https://api.github.com/users/alice');
  expect(user.data.login).toBe('alice');
});
```

---

### 2. Database

| Good | Bad | Detection | Fix |
|------|-----|-----------|-----|
| In-memory (`sqlite :memory:`) or mocked | Real PostgreSQL/MySQL | Check connection strings (`localhost:5432`, real DB URL) | Use `:memory:` or mock DB |

**Example (Bad):**
```javascript
beforeAll(async () => {
  await db.connect('postgresql://localhost:5432/testdb'); // Real DB
});
```

**Example (Good):**
```javascript
beforeAll(async () => {
  await db.connect('sqlite::memory:'); // In-memory
});
```

---

### 3. File System

| Good | Bad | Detection | Fix |
|------|-----|-----------|-----|
| Mocked (`mock-fs`, `memfs`) | Real `fs.readFile`, `fs.writeFile` | Grep for `fs.readFile` without mocks | Mock with `mock-fs` |

**Example (Bad):**
```javascript
test('reads file', () => {
  const content = fs.readFileSync('/tmp/test.txt'); // Real file
  expect(content).toBe('data');
});
```

**Example (Good):**
```javascript
const mockFs = require('mock-fs');

test('reads file', () => {
  mockFs({ '/tmp/test.txt': 'data' });

  const content = fs.readFileSync('/tmp/test.txt');
  expect(content).toBe('data');

  mockFs.restore();
});
```

---

### 4. Time/Date

| Good | Bad | Detection | Fix |
|------|-----|-----------|-----|
| Mocked (`jest.useFakeTimers`, `sinon.useFakeTimers`) | `new Date()`, `Date.now()` without mocks | Grep for `new Date()` in tests | Mock with `jest.useFakeTimers()` |

**Example (Bad):**
```javascript
test('checks expiry', () => {
  const token = { expiresAt: Date.now() + 1000 }; // Real time
  expect(isExpired(token)).toBe(false);
});
```

**Example (Good):**
```javascript
test('checks expiry', () => {
  jest.useFakeTimers().setSystemTime(new Date('2025-01-01'));

  const token = { expiresAt: new Date('2025-01-02').getTime() };
  expect(isExpired(token)).toBe(false);
});
```

---

### 5. Random

| Good | Bad | Detection | Fix |
|------|-----|-----------|-----|
| Seeded (`Math.seedrandom`, fixed seed) | `Math.random()` without seed | Grep for `Math.random()` | Use seeded random |

**Example (Bad):**
```javascript
test('generates random ID', () => {
  const id = generateId(); // Uses Math.random()
  expect(id).toHaveLength(10); // Flaky if random changes
});
```

**Example (Good):**
```javascript
const seedrandom = require('seedrandom');

test('generates random ID', () => {
  Math.random = seedrandom('test-seed'); // Fixed seed

  const id = generateId();
  expect(id).toBe('abc123xyz4'); // Deterministic
});
```

---

### 6. Network

| Good | Bad | Detection | Fix |
|------|-----|-----------|-----|
| Mocked (`supertest`, no real ports) | Real HTTP server (`app.listen(3000)`) | Grep for `app.listen(` in tests | Use `supertest` |

**Example (Bad):**
```javascript
beforeAll(async () => {
  await app.listen(3000); // Real port
});

test('GET /users', async () => {
  const response = await axios.get('http://localhost:3000/users'); // Real network
  expect(response.status).toBe(200);
});
```

**Example (Good):**
```javascript
test('GET /users', async () => {
  const response = await request(app).get('/users'); // No real port
  expect(response.status).toBe(200);
});
```

---

## Determinism Checklist

| Issue | Detection | Fix |
|-------|-----------|-----|
| **Flaky tests** | Run tests 5 times, check for inconsistency | Fix race conditions, proper async/await |
| **Time-dependent** | Grep for `Date.now()` in assertions | Mock time |
| **Order-dependent** | Run tests in random order (`jest --random`) | Isolate state, use `beforeEach` |
| **Shared state** | Grep for `let globalVar` at module level | Reset state in `beforeEach` |

---

## Anti-Patterns Catalog (6 Types)

### 1. The Liar (Always Passes)

**What:** Test with no assertions or trivial assertion.

**Detection:**
- Count assertions per test
- If 0 assertions OR only `toBeTruthy()` → Liar

**Severity:** **HIGH**

**Example (Bad):**
```javascript
test('user creation works', async () => {
  await createUser({ name: 'Alice' });
  // NO ASSERTION — test always passes
});
```

**Fix:**
```javascript
test('user creation works', async () => {
  const user = await createUser({ name: 'Alice' });
  expect(user.name).toBe('Alice');
  expect(user.id).toBeDefined();
});
```

---

### 2. The Giant (>100 lines)

**What:** Test >100 lines, testing too many scenarios.

**Detection:** Count lines per test

**Severity:** **MEDIUM**

**Example (Bad):**
```javascript
test('order flow', async () => {
  // 150 lines testing:
  // - Create order
  // - Add items
  // - Apply discount
  // - Calculate tax
  // - Process payment
  // - Send email
  // - Update inventory
  // - ...
});
```

**Fix:** Split into focused tests (one scenario per test):
```javascript
test('creates order with valid data', async () => { /* ... */ });
test('applies discount code correctly', async () => { /* ... */ });
test('processes payment successfully', async () => { /* ... */ });
```

---

### 3. Slow Poke (>5 seconds)

**What:** Test taking >5 seconds.

**Detection:** Measure test duration

**Severity:** **MEDIUM**

**Causes:**
- Real DB/API calls
- Unoptimized queries
- No parallelization

**Fix:**
- Mock external dependencies
- Use in-memory DB
- Parallelize tests (`jest --maxWorkers=4`)

---

### 4. Conjoined Twins (Unit test without mocks = Integration)

**What:** Test labeled "Unit" but calling real dependencies.

**Detection:**
- Check if test name includes "Unit"
- Verify all dependencies mocked

**Severity:** **LOW**

**Example (Bad):**
```javascript
// Labeled "Unit" but calling real DB
test('[Unit] createUser inserts into database', async () => {
  const user = await createUser({ name: 'Alice' }); // Real DB call
  expect(user.id).toBeDefined();
});
```

**Fix:** Either mock DB OR rename to Integration:
```javascript
test('[Integration] createUser inserts into database', async () => {
  const user = await createUser({ name: 'Alice' });
  expect(user.id).toBeDefined();
});
```

---

### 5. Happy Path Only (No error scenarios)

**What:** Only testing success, ignoring errors.

**Detection:** Check if negative tests exist for each function.

**Severity:** **MEDIUM**

**Example (Bad):**
```javascript
// Only positive test
test('login with valid credentials', async () => {
  const result = await login('alice@example.com', 'password123');
  expect(result.token).toBeDefined();
});
```

**Fix:** Add negative test:
```javascript
test('login with invalid credentials returns error', async () => {
  await expect(login('alice@example.com', 'wrong')).rejects.toThrow('Invalid credentials');
});
```

---

### 6. Framework Tester (Tests framework behavior)

**What:** Tests validating Express/Prisma/bcrypt (not OUR code).

**Detection:** Cross-reference with ln-631-test-business-logic-auditor findings.

**Severity:** **MEDIUM**

**Example (Bad):**
```javascript
test('Express middleware is called', async () => {
  const middleware = jest.fn((req, res, next) => next());
  app.use(middleware);

  await request(app).get('/');
  expect(middleware).toHaveBeenCalled(); // Testing Express, not our logic
});
```

**Decision:** REMOVE — Express already tested by maintainers.

---
**Version:** 1.0.0
**Last Updated:** 2025-12-21
