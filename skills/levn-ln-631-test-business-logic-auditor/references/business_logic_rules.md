# Business Logic Focus Audit Rules

<!-- SCOPE: Framework/library test detection patterns ONLY. Contains regex patterns, DELETE/KEEP decisions. -->
<!-- DO NOT add here: Audit workflow → ln-631-test-business-logic-auditor SKILL.md -->

Framework/library test detection patterns and examples.

## Detection Patterns (Regex)

### Web Frameworks

| Framework | Pattern | Example Test Names |
|-----------|---------|-------------------|
| Express | `(express\|app)\.(use\|get\|post\|put\|delete\|patch\|listen)` | "middleware is called", "route handler works", "Express app listens" |
| Fastify | `(fastify\|server)\.(register\|get\|post\|put\|delete\|addHook)` | "Fastify plugin loads", "route is registered" |
| Koa | `(koa\|ctx)\.(use\|get\|post\|body\|status)` | "Koa middleware executes", "ctx.body is set" |

**Decision:** DELETE — frameworks already tested by maintainers

### ORMs / Database Libraries

| ORM | Pattern | Example Test Names |
|-----|---------|-------------------|
| Prisma | `prisma\.(find\|findMany\|findUnique\|create\|update\|delete\|upsert)` | "Prisma findMany returns array", "Prisma create works" |
| Mongoose | `(mongoose\|Model)\.(find\|save\|create\|updateOne\|deleteOne)` | "Mongoose save persists data", "Model.find returns docs" |
| Sequelize | `(sequelize\|Model)\.(findAll\|findOne\|create\|update\|destroy)` | "Sequelize findAll works", "Model.create inserts row" |
| TypeORM | `(typeorm\|repository)\.(find\|save\|remove\|update)` | "TypeORM repository saves entity" |

**Decision:** DELETE — ORMs already tested

### Crypto / Hashing Libraries

| Library | Pattern | Example Test Names |
|---------|---------|-------------------|
| bcrypt | `bcrypt\.(hash\|hashSync\|compare\|compareSync\|genSalt)` | "bcrypt hashes password", "bcrypt compare works" |
| argon2 | `argon2\.(hash\|verify\|hashRaw)` | "argon2 hashes securely", "argon2 verify returns true" |

**Decision:** DELETE — crypto libraries already tested

**Exception:** Keep if testing OUR custom password policy (length, complexity), not bcrypt itself.

### JWT / Token Libraries

| Library | Pattern | Example Test Names |
|---------|---------|-------------------|
| jsonwebtoken | `(jwt\|jsonwebtoken)\.(sign\|verify\|decode)` | "JWT signs token", "JWT verifies signature", "JWT decodes payload" |

**Decision:** DELETE — JWT library already tested

**Exception:** Keep if testing OUR custom claims/expiry logic.

### HTTP Client Libraries

| Library | Pattern | Example Test Names |
|---------|---------|-------------------|
| axios | `axios\.(get\|post\|put\|delete\|patch\|request)` | "axios makes GET request", "axios posts data" |
| fetch | `fetch\(.*\)\.then` | "fetch returns response", "fetch handles errors" |
| got | `got\.(get\|post\|put\|delete)` | "got makes HTTP call" |

**Decision:** DELETE — HTTP clients already tested

**Exception:** Keep if testing OUR API client wrapper logic.

### React Hooks (Frontend)

| Hook | Pattern | Example Test Names |
|------|---------|-------------------|
| useState | `useState\(` | "useState updates state", "useState initial value" |
| useEffect | `useEffect\(` | "useEffect runs on mount", "useEffect cleanup" |
| useContext | `useContext\(` | "useContext provides value" |
| Custom hooks | `use[A-Z][a-zA-Z]+\(` | **REVIEW** — if testing framework behavior → DELETE; if testing custom hook logic → KEEP |

**Decision:**
- Built-in hooks (useState, useEffect, etc.) → DELETE
- Custom hooks testing OUR logic → KEEP

## Good vs Bad Examples

### Example 1: Framework Test (BAD)

```javascript
// BAD — Tests Express framework, not OUR code
test('Express middleware is called', async () => {
  const app = express();
  const middleware = jest.fn((req, res, next) => next());
  app.use(middleware);

  await request(app).get('/');
  expect(middleware).toHaveBeenCalled(); // Testing Express, not our logic
});
```

**Decision:** REMOVE (Usefulness Score: 2)

### Example 2: Business Logic Test (GOOD)

```javascript
// GOOD — Tests OUR discount calculation logic
test('applies 20% discount for bulk orders', async () => {
  const order = { items: 15, price: 100 };
  const total = calculateDiscount(order);

  expect(total).toBe(80); // Testing OUR logic, not framework
});
```

**Decision:** KEEP (Usefulness Score: 18)

### Example 3: ORM Test (BAD)

```javascript
// BAD — Tests Prisma ORM, not OUR code
test('Prisma findMany returns array', async () => {
  const users = await prisma.user.findMany();
  expect(Array.isArray(users)).toBe(true); // Testing Prisma, not our logic
});
```

**Decision:** REMOVE (Usefulness Score: 4)

### Example 4: Query Logic Test (GOOD)

```javascript
// GOOD — Tests OUR complex query logic
test('getUsersByRole filters correctly', async () => {
  const admins = await getUsersByRole('admin');

  expect(admins.every(u => u.role === 'admin')).toBe(true); // Testing OUR filtering logic
});
```

**Decision:** KEEP (Usefulness Score: 15)

## Edge Cases

### Custom Wrapper Around Library (REVIEW)

```javascript
// Custom bcrypt wrapper with password policy
export async function hashPasswordWithPolicy(password: string) {
  if (password.length < 12) throw new Error('Too short');
  if (!/[A-Z]/.test(password)) throw new Error('Needs uppercase');

  return bcrypt.hash(password, 10); // Library call
}

// Test for custom wrapper (KEEP)
test('hashPasswordWithPolicy enforces 12 char minimum', async () => {
  await expect(hashPasswordWithPolicy('short')).rejects.toThrow('Too short');
});
```

**Decision:** KEEP — tests OUR password policy, not bcrypt itself (Usefulness Score: 16)

---
**Version:** 1.0.0
**Last Updated:** 2025-12-21
