# Coverage Gaps Audit Rules

<!-- SCOPE: Critical paths classification for coverage gaps ONLY. Contains priority keywords (money, auth, data), detection patterns. -->
<!-- DO NOT add here: Audit workflow → ln-634-test-coverage-auditor SKILL.md -->

Critical paths classification and missing test identification.

## Critical Paths Classification

### 1. Money Flows (Priority 20+)

**Definition:** Any code handling financial transactions, calculations, or currency.

**Detection Keywords:**
- `payment`, `pay`, `charge`, `refund`, `invoice`, `bill`
- `discount`, `coupon`, `promo`, `price`, `total`, `tax`
- `currency`, `exchange`, `convert`

**Examples:**

| Code Path | Priority | Justification |
|-----------|----------|---------------|
| `processPayment(order)` | 25 | Money loss if calculation wrong |
| `calculateDiscount(promoCode)` | 22 | Revenue impact, fraud risk |
| `calculateTax(amount, country)` | 20 | Legal compliance, accuracy |
| `processRefund(orderId)` | 24 | Money loss, customer trust |
| `convertCurrency(amount, from, to)` | 20 | Financial accuracy |

**Min Priority:** 20

---

### 2. Security Flows (Priority 20+)

**Definition:** Authentication, authorization, encryption, sensitive data handling.

**Detection Keywords:**
- `auth`, `login`, `logout`, `register`, `password`, `token`
- `permission`, `role`, `access`, `authorize`
- `encrypt`, `decrypt`, `hash`, `verify`, `sign`
- `secret`, `key`, `credential`

**Examples:**

| Code Path | Priority | Justification |
|-----------|----------|---------------|
| `login(email, password)` | 25 | Security breach if broken |
| `resetPassword(token, newPassword)` | 23 | Account takeover risk |
| `checkPermission(user, resource)` | 22 | Authorization bypass risk |
| `refreshAccessToken(refreshToken)` | 20 | Session hijacking risk |
| `validateApiKey(key)` | 21 | Unauthorized API access |

**Min Priority:** 20

---

### 3. Data Integrity (Priority 15+)

**Definition:** CRUD operations, transactions, validation, data migrations.

**Detection Keywords:**
- `create`, `update`, `delete`, `save`, `persist`
- `transaction`, `commit`, `rollback`
- `validate`, `sanitize`, `check`, `verify`
- `migration`, `migrate`, `schema`
- `unique`, `constraint`, `duplicate`

**Examples:**

| Code Path | Priority | Justification |
|-----------|----------|---------------|
| `createUser(data)` | 18 | Data corruption if validation fails |
| `withTransaction(() => { ... })` | 19 | Data inconsistency if rollback fails |
| `validateUniqueEmail(email)` | 16 | Duplicate users, data integrity |
| `migrateData(fromV1toV2)` | 20 | Data loss risk |
| `deleteOrder(orderId)` | 17 | Accidental deletion, cascade issues |

**Min Priority:** 15

---

### 4. Core User Journeys (Priority 15+)

**Definition:** Multi-step workflows critical to business value.

**Detection Patterns:**
- Multiple endpoints in sequence
- State machines, workflow engines
- Multi-page flows (registration, checkout, onboarding)

**Examples:**

| Journey | Priority | Justification |
|---------|----------|---------------|
| Registration → Email verify → First login | 18 | Broken onboarding = lost users |
| Search → Product → Add to cart → Checkout → Payment | 20 | Core revenue flow |
| Upload file → Process → Download result | 16 | Main feature broken |
| Submit ticket → Approval → Notification | 15 | Business process broken |

**Min Priority:** 15

---

## Missing Test Identification

### Process

1. **Scan codebase** for critical keywords (money, auth, etc.)
2. **Identify critical paths** (functions, endpoints, flows)
3. **Check test coverage** for each critical path
4. **If NO test found** → add to missing tests list
5. **If test inadequate** (only positive, no edge cases) → add to gaps list

### Gap Types

| Gap Type | Description | Example |
|----------|-------------|---------|
| **No test** | Critical path completely untested | `processRefund()` has 0 tests |
| **Only positive** | No error handling tested | `login()` tested only for success, not 401 |
| **No edge cases** | Only happy path tested | `calculateTax()` tested for US, not 49 other countries |
| **Integration missing** | Unit tests exist, but no E2E/Integration | `payment` unit tested, no E2E for `/payment` endpoint |

### Output Format

**For each missing test:**
- **Severity:** CRITICAL (Priority 20+) | HIGH (Priority 15-19) | MEDIUM (Priority 10-14)
- **Category:** Money | Security | Data Integrity | Core Flow
- **Missing test description:** E2E/Integration/Unit + scenario
- **Location:** File:function or route
- **Priority:** Calculated Usefulness Score
- **Justification:** Why critical (money loss, security, etc.)
- **Test type recommendation:** E2E | Integration | Unit
- **Effort:** S | M | L

---

## Examples

### Example 1: Missing Payment Test

```javascript
// Code exists
export async function processPayment(order: Order, promoCode?: string) {
  const discount = promoCode ? await getDiscount(promoCode) : 0;
  const tax = calculateTax(order.amount, order.country);
  const total = order.amount - discount + tax;

  return await chargeCard(order.cardToken, total);
}

// NO TEST FOUND
```

**Missing Test:**
```json
{
  "severity": "CRITICAL",
  "category": "Money",
  "missing_test": "E2E: POST /payment with promo code applies discount correctly",
  "location": "services/payment.ts:processPayment()",
  "priority": 25,
  "justification": "Money calculation with discount/tax — high risk of incorrect charge",
  "test_type": "E2E",
  "effort": "M"
}
```

### Example 2: Missing Error Handling Test

```javascript
// Code exists
app.get('/users/:id', async (req, res) => {
  const user = await getUserById(req.params.id);
  if (!user) return res.status(404).json({ error: 'Not found' });
  res.json(user);
});

// Positive test exists (GOOD)
test('GET /users/:id returns user', async () => {
  const response = await request(app).get('/users/123');
  expect(response.status).toBe(200);
});

// Negative test MISSING (GAP)
```

**Missing Test:**
```json
{
  "severity": "MEDIUM",
  "category": "Core Flow",
  "missing_test": "E2E: GET /users/:id returns 404 for nonexistent user",
  "location": "routes/users.ts:10",
  "priority": 12,
  "justification": "Error handling untested — 404 scenario not covered",
  "test_type": "E2E",
  "effort": "S"
}
```

---
**Version:** 1.0.0
**Last Updated:** 2025-12-21
