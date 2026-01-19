# Usefulness Score Calculation Guide

Impact × Probability matrix for risk-based test value assessment.

## Scoring Formula

```
Usefulness Score = Business Impact (1-5) × Failure Probability (1-5)
Range: 1-25
```

## Impact Matrix (1-5)

| Score | Impact | Business Consequence | Examples |
|-------|--------|---------------------|----------|
| **5** | **Critical** | Money loss, security breach, data corruption, legal liability | Payment processing, tax calculation, refunds, authentication, encryption, GDPR compliance |
| **4** | **High** | Core flow breaks, major feature unusable | Checkout, login, registration, search, file upload |
| **3** | **Medium** | Feature partially broken, degraded UX, workaround exists | Filter doesn't work, slow performance, minor UI glitch |
| **2** | **Low** | Minor UX issue, cosmetic bug, no functional impact | Typo in UI, misaligned button, tooltip missing |
| **1** | **Trivial** | Cosmetic issue, no user-facing impact | Internal variable naming, unused code path |

### Impact Examples

**Impact 5 (Critical):**
- `calculateRefund(order)` — money loss if wrong
- `hashPassword(password)` — security breach if broken
- `exportGDPRData(userId)` — legal liability

**Impact 4 (High):**
- `checkout(cart)` — can't complete purchase
- `login(email, password)` — can't access account
- `uploadFile(file)` — core feature broken

**Impact 3 (Medium):**
- `filterProductsByPrice(min, max)` — search degraded, but usable
- `sortComments(order)` — minor UX issue

**Impact 2 (Low):**
- `formatDate(date, locale)` — cosmetic, doesn't break flow
- `validateEmail(email)` — already validated client-side

**Impact 1 (Trivial):**
- `getUserDisplayName(user)` — trivial getter
- `const COLORS = { red: '#FF0000' }` — constant value

## Probability Matrix (1-5)

| Score | Probability | Indicators | Examples |
|-------|-------------|------------|----------|
| **5** | **Very High** | Complex algorithm, new technology, many dependencies, untested pattern | Multi-step payment with discounts/taxes/currency conversion, new ML model integration |
| **4** | **High** | Multiple dependencies, concurrency, edge cases, external APIs | Async workflows, race conditions, third-party API integration |
| **3** | **Medium** | Standard CRUD, framework defaults, established patterns | Basic REST endpoints, simple queries, standard validation |
| **2** | **Low** | Simple logic, well-established library, minimal dependencies | Trivial calculations, standard library functions |
| **1** | **Very Low** | Trivial assignment, framework-generated, impossible to break | Constant getters, framework scaffolding |

### Probability Examples

**Probability 5 (Very High):**
- `calculatePaymentWithDiscountAndTax(order, promoCode, country)` — complex, many edge cases
- `processConcurrentOrders(orders)` — race conditions possible

**Probability 4 (High):**
- `syncDataWithExternalAPI(userId)` — external dependency, network issues
- `applyBusinessRules(data)` — multiple rules, interactions

**Probability 3 (Medium):**
- `createUser(data)` — standard CRUD
- `validatePassword(password)` — established pattern

**Probability 2 (Low):**
- `add(a, b)` — trivial calculation
- `formatString(str)` — simple transformation

**Probability 1 (Very Low):**
- `getUserId(user)` — constant getter
- `return true` — impossible to break

## Decision Thresholds

| Score Range | Decision | Justification | Action |
|-------------|----------|---------------|--------|
| **20-25** | **KEEP** | Critical + Very High probability | Essential test, maintain |
| **15-19** | **KEEP** | High value (Critical×Medium or High×High) | Valuable test, maintain |
| **10-14** | **REVIEW** | Medium value | Ask: "Is this covered by E2E?" If yes → REMOVE; else → KEEP |
| **6-9** | **REMOVE** | Low value | Delete, not worth maintenance |
| **1-5** | **REMOVE** | Trivial value | Delete immediately |

## Scoring Examples

### Example 1: Payment with Discount (Score 20)

```javascript
test('processPayment applies 20% discount correctly', async () => {
  const order = { amount: 100, promoCode: 'SAVE20' };
  const result = await processPayment(order);
  expect(result.total).toBe(80);
});
```

**Impact:** 5 (Critical — money calculation)
**Probability:** 4 (High — complex discount logic, promo code validation)
**Score:** 5 × 4 = **20**
**Decision:** **KEEP** — essential test for money flow

### Example 2: Email Validation (Score 4)

```javascript
test('validateEmail returns true for valid email', () => {
  expect(validateEmail('user@example.com')).toBe(true);
});
```

**Impact:** 2 (Low — minor UX issue, already validated client-side)
**Probability:** 2 (Low — simple regex, established pattern)
**Score:** 2 × 2 = **4**
**Decision:** **REMOVE** — likely covered by E2E registration test

### Example 3: Login Flow (Score 12)

```javascript
test('login with valid credentials returns JWT', async () => {
  const result = await login('user@example.com', 'password123');
  expect(result.token).toBeDefined();
});
```

**Impact:** 4 (High — core flow)
**Probability:** 3 (Medium — standard auth pattern)
**Score:** 4 × 3 = **12**
**Decision:** **REVIEW** — Check if E2E login test already covers this. If yes → REMOVE (duplicate); if no → KEEP

### Example 4: Getter Function (Score 1)

```javascript
test('getUserId returns user.id', () => {
  const user = { id: 123, name: 'Alice' };
  expect(getUserId(user)).toBe(123);
});
```

**Impact:** 1 (Trivial — no business impact)
**Probability:** 1 (Very Low — impossible to break)
**Score:** 1 × 1 = **1**
**Decision:** **REMOVE** — wasteful test

## Decision Flow

```
Calculate Usefulness Score
         |
         v
     Score ≥ 15?
      /     \
    Yes      No
     |        |
    KEEP      |
         Score 10-14?
          /      \
        Yes       No
         |        |
      REVIEW   REMOVE
         |
  Is E2E covering?
      /      \
    Yes       No
     |        |
  REMOVE    KEEP
```

---
**Version:** 1.0.0
**Last Updated:** 2025-12-21
