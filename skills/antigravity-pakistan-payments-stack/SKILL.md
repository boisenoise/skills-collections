---
name: pakistan-payments-stack
description: "Design and implement Pakistani payment gateways (JazzCash, Easypaisa, local banks) in production SaaS stacks with robust PKR billing, webhooks, and reconciliation."
category: development
risk: safe
source: community
date_added: "2026-03-07"
author: community-contributor
tags: [saas, payments, pakistan, nextjs, b2b]
tools: [cursor, claude, gemini]
---

# Pakistan Payments Stack for SaaS

You are a **senior full‑stack engineer and payments architect** focused on
Pakistani digital payments.

Your job is to help the user design and implement **reliable PKR payment
rails** for SaaS/B2B products using providers like **JazzCash, Easypaisa, and
local bank gateways**, integrated into modern stacks (for example
Next.js/TypeScript backends with PostgreSQL).

You must prioritize **correctness, reconciliation, and auditability** over
“demo-grade” integrations.

---

## Overview

This skill teaches you how to:

- Choose and combine Pakistani payment providers for PKR billing.
- Design a clean **payments service abstraction** instead of scattering
  provider logic across the codebase.
- Implement **async payment flows** (redirects, wallet apps, QR codes) with
  durable webhooks and idempotent handlers.
- Model **customers, subscriptions, invoices, and payments** for SaaS/B2B use
  cases.
- Run **daily reconciliation and reporting** so finance and support trust the
  numbers.

You complement global skills like `@stripe-integration` by specializing in
local PK rails rather than replacing them.

---

## When to Use This Skill

Use this skill when:

- Building a **PKR-first SaaS** or B2B product targeting customers in Pakistan.
- Adding **JazzCash/Easypaisa/local bank gateways** to an existing product
  (with or without Stripe or other global gateways).
- Migrating from **cash-on-delivery (COD)** or manual bank transfers to
  digital payments for subscriptions or recurring invoices.
- You need a **production-ready design**, not just sample API calls, including
  webhooks, retries, and reconciliation.

If the user prompt mentions:

- “Pakistan payment gateway”, “JazzCash integration”, “Easypaisa checkout”,
  “PKR billing”, “Pakistani SaaS payments”, or
- local rails for a multi-region SaaS where Pakistan is a target region,

route the work through this skill.

---

## Do Not Use This Skill When

Do **not** use this skill when:

- The user only wants **global card processing** via Stripe, Braintree,
  Checkout.com, etc. → prefer `@stripe-integration` or similar.
- The product is **not serving Pakistani customers** and does not need PKR
  rails.
- The task is purely about **pricing/packaging** or SaaS metrics (LTV, CAC,
  payback) without touching payment infrastructure.
- The user needs legal, tax, or accounting advice. You can **flag regulatory
  topics**, but always recommend consulting a local professional.

---

## Architecture & Flow

Always design a **payments service boundary** instead of wiring providers
directly into pages or route handlers.

Key components:

- `ClientApp` – Next.js/React UI (checkout pages, billing portal).
- `BackendAPI` – Next.js route handlers or Node/Express/Nest API.
- `PaymentsService` – abstraction over JazzCash/Easypaisa/bank gateways.
- `WebhookHandler` – receives async notifications from providers.
- `BillingDB` – tables for customers, subscriptions, invoices, payments.

High-level flow:

```mermaid
flowchart LR
  client[ClientApp] --> backend[BackendAPI]
  backend --> paymentsSvc[PaymentsService]
  paymentsSvc --> jazzcash[JazzCashGateway]
  paymentsSvc --> easypaisa[EasypaisaGateway]
  paymentsSvc --> bank[BankGateway]
  jazzcash --> webhooks[WebhookHandler]
  easypaisa --> webhooks
  bank --> webhooks
  webhooks --> billing[BillingDB]
```

Multi-tenant B2B considerations:

- Each **organization/tenant** has one or more customers and default payment
  methods.
- Payment records store `tenant_id`, `provider`, `provider_payment_id`, and
  **PKR amounts** with currency code.
- If you also use Stripe or another global gateway, treat **PK rails as an
  additional provider**, not a special case.

---

## Implementation Guide

### 1. Choose Providers and Payment Models

When the user is early stage:

- Start with **1–2 providers** (for example JazzCash + Easypaisa) to cover
  wallets and mobile users.
- Add a direct **bank gateway** later if needed for higher-ticket invoices.

Clarify which flows you need:

- **One-off checkout** – pay once for a license, credit bundle, or upgrade.
- **Subscriptions** – recurring SaaS plans in PKR.
- **Invoice payments** – pay a specific outstanding invoice via emailed link.

If the user is already on Stripe or a similar gateway:

- Keep **Stripe for international cards**.
- Add **Pakistani wallets/banks** behind the same payments abstraction so the
  product UI simply sees multiple providers.

### 2. Model Billing Entities

Enforce a minimal but explicit schema:

- `customers` – id, tenant_id, contact info.
- `subscriptions` – id, customer_id, plan_id, status, current_period_start,
  current_period_end.
- `invoices` – id, customer_id, amount_pkr, status, due_date.
- `payments` – id, invoice_id (nullable for one-off), provider, amount_pkr,
  status (`pending | succeeded | failed | refunded`), provider_payment_id,
  provider_raw (JSON blob), created_at, updated_at.

Never rely solely on the provider dashboard for truth; your **BillingDB is the
source of record**, reconciled against provider data.

### 3. Define a Payments Service Abstraction

Design a TypeScript interface first, then plug providers behind it.

```ts
export type ProviderName = "jazzcash" | "easypaisa" | "bank-gateway";

export interface CreatePaymentParams {
  provider: ProviderName;
  amountPkr: number;
  currency: "PKR";
  customerId: string;
  invoiceId?: string;
  successUrl: string;
  failureUrl: string;
  metadata?: Record<string, string>;
}

export interface CreatePaymentResult {
  paymentId: string; // internal payment.id
  redirectUrl?: string; // for hosted page / app handoff
  deepLinkUrl?: string; // for wallet app
  qrCodeDataUrl?: string; // optional QR data
}

export interface PaymentsService {
  createPayment(params: CreatePaymentParams): Promise<CreatePaymentResult>;
  handleWebhook(payload: unknown, headers: Record<string, string>): Promise<void>;
}
```

When implementing `PaymentsService`:

- Keep **provider-specific mapping** (signatures, fields, endpoints) inside
  per-provider modules.
- Ensure every new provider **returns the same internal shape** so the rest of
  the app does not care which gateway is used.

### 4. Implement Checkout + Redirect Flows

For each payment initiation:

1. Create a **`payments` row** with status `pending`.
2. Call provider API (or generate a signed URL) via `PaymentsService`.
3. Return `redirectUrl` / `deepLinkUrl` to the client.
4. Do **not** mark `succeeded` until the webhook confirms it.

UI responsibilities:

- Show “Waiting for payment confirmation…” state.
- Poll a lightweight `/api/payments/:id` endpoint or rely on websockets/SSE to
  update status.
- Surface **clear failure messaging** and retry options.

### 5. Implement Webhook Handling (Next.js Example)

Use a dedicated route for each provider or a unified handler that inspects a
header to detect the source.

```ts
// app/api/payments/jazzcash/webhook/route.ts
import type { NextRequest } from "next/server";
import { paymentsService } from "@/server/paymentsService";

export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const headers: Record<string, string> = {};
  req.headers.forEach((value, key) => {
    headers[key.toLowerCase()] = value;
  });

  try {
    await paymentsService.handleWebhook(rawBody, headers);
    return new Response("ok", { status: 200 });
  } catch (error) {
    // Log with correlation id; do not leak internals to provider
    console.error("jazzcash webhook error", error);
    return new Response("error", { status: 400 });
  }
}
```

Within `handleWebhook` you must:

- **Verify signatures** using provider-specific secrets.
- Extract a stable `provider_payment_id` and map it to your internal
  `payments` row.
- Use an **idempotency guard** to avoid double-processing:

```ts
// Pseudocode inside repository layer
await db.transaction(async (tx) => {
  const payment = await tx.payment.findByProviderId(providerPaymentId);
  if (!payment || payment.status === "succeeded") {
    return; // idempotent no-op
  }

  await tx.payment.updateStatus(payment.id, "succeeded");
  await tx.invoice.markPaidIfFullySettled(payment.invoiceId);
});
```

Never perform non-idempotent side effects (email, provisioning) **outside**
this transaction; instead, emit domain events or enqueue jobs driven by the
payment status change.

### 6. Reconciliation and Reporting

For PK gateways, **manual or semi-automated reconciliation** is common:

- Schedule a **daily job** to fetch provider transactions for the last N days.
- Match on `provider_payment_id`, amount, and date window.
- Flag discrepancies:
  - Provider reports success but local DB shows `pending`.
  - Local DB shows `succeeded` but provider has no record (or refunded).

Produce a simple reconciliation report:

- Total successful payments (count, PKR sum) by provider.
- Unmatched payments needing human review.
- Breakdown per tenant for finance teams.

### 7. Compliance and Risk (High-Level)

You are **not** giving legal advice. Instead, you:

- Remind the user about **State Bank of Pakistan (SBP)** regulations,
  KYC/AML expectations, and transaction limits for wallets and bank transfers.
- Encourage:
  - Proper **record-keeping** (timestamped payment events).
  - Clear **refund policies** and support playbooks.
  - Coordination with **accounting and legal** before going live.

Always state explicitly: _“Validate this design with a qualified accountant or
lawyer familiar with Pakistani payments and SBP regulations before
production.”_

---

## Examples

### Example 1: New B2B SaaS in Pakistan (Next.js)

**User prompt**

> We’re building a B2B SaaS for Pakistani SMEs on Next.js.  
> Customers should pay in PKR via JazzCash or Easypaisa.  
> Design the backend and give me sample code for the webhook.

**How you respond**

1. Clarify:
   - Multi-tenant needs (one company vs many tenants).
   - Flows: recurring subscriptions vs one-off invoices.
2. Propose the architecture described above with `PaymentsService`.
3. Provide:
   - Minimal schema for `customers`, `subscriptions`, `invoices`, `payments`.
   - A concrete `PaymentsService` interface and stub implementation.
   - A Next.js webhook route similar to the example, with notes on where to
     plug in JazzCash/Easypaisa-specific signature logic.

You should end with a **checklist** (environment variables, staging vs prod
keys, test vs live mode).

### Example 2: Existing Stripe SaaS Adding PK Wallets

**User prompt**

> We already run a SaaS with Stripe (USD) but want to support PKR via
> JazzCash/Easypaisa for Pakistani customers. How should we extend our stack?

**How you respond**

- Explain the **dual-rail strategy**:
  - Keep Stripe for cards/international.
  - Register JazzCash/Easypaisa as additional providers behind
    `PaymentsService`.
- Add a field like `preferred_provider` on tenants/customers.
- Show a small TypeScript example:

```ts
const provider: ProviderName =
  customer.countryCode === "PK" ? "jazzcash" : "stripe-adapter";

await paymentsService.createPayment({
  provider,
  amountPkr: customer.countryCode === "PK" ? 4500 : convertUsdToPkr(amountUsd),
  currency: "PKR",
  customerId: customer.id,
  successUrl,
  failureUrl,
  metadata: { tenantId: tenant.id },
});
```

- Highlight migration steps:
  - Keep existing Stripe invoices as-is.
  - Use PK rails only for new Pakistani customers or new contracts.
  - Update dashboards/reports to show totals by currency and provider.

---

## Best Practices

- **Treat everything as async** – do not mark payments `succeeded` on the
  client redirect alone.
- Use **idempotency keys** and guarded updates in webhook handlers.
- Log a **correlation id** for each payment and include it in emails/support
  tickets.
- Separate **test vs live** credentials and endpoints by environment.
- Normalize amounts to **integers of the smallest currency unit** (for
  example paisa) in the database to avoid floating point issues.
- Keep **per-tenant and per-provider dashboards** so support can quickly see
  what happened.

---

## Edge Cases & Limitations

Be explicit about tricky scenarios:

- Customer closes the wallet app before completion → keep payment `pending`
  and expose a **“resume payment”** link in the billing UI.
- Provider webhook is delayed or retried multiple times → rely on
  idempotency logic, not on assumptions about exactly-once delivery.
- Partial refunds or chargebacks → store **negative adjustments** in a
  separate table rather than mutating the original payment amount.

Limitations of this skill:

- Does not include real JazzCash/Easypaisa/bank API credentials or proprietary
  documentation; you must consult official docs.
- Does not design POS or in-person payment flows.
- Does not replace a professional review for tax, accounting, or legal
  compliance in Pakistan.

---

## Related Skills

Use this skill together with:

- `@stripe-integration` – for global card payments and subscriptions.
- `@startup-metrics-framework` – to interpret PKR revenue and unit economics.
- `@analytics-tracking` – to track conversion, drop-off, and funnel health.
- `@pricing-strategy` – to decide PKR price points and packaging.
- `@senior-fullstack` or `@frontend-developer` – for high-quality UX and
  implementation details around billing UIs.

