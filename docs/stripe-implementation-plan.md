# Stripe Implementation Plan

Status: **Phase 1 planning only**. Stripe code must not be written until these implementation steps are reviewed and approved.

## Phase 1 Scope Guardrails

- Do not install the Stripe SDK in this planning phase.
- Do not add live or test Stripe secrets to the repository.
- Do not create billing routes, database migrations, frontend checkout calls, webhook handlers, or role-changing code until the plan is reviewed.
- Treat Stripe as the future source of truth for paid membership state after implementation is approved.

## Executable Implementation Steps

### 1. Stripe Products And Prices

1. In the Stripe Dashboard, create a product named `Community Member`.
2. Add one recurring monthly price for `Community Member`:
   - Amount: `$10.00`
   - Billing interval: monthly
   - Currency: `USD`
   - Lookup key: `community_member_monthly`
3. In the Stripe Dashboard, create a product named `Builder Member`.
4. Add one recurring monthly price for `Builder Member`:
   - Amount: `$25.00`
   - Billing interval: monthly
   - Currency: `USD`
   - Lookup key: `builder_member_monthly`
5. Store the resulting Stripe price IDs in environment variables rather than hard-coding them.
6. Record whether the IDs are test-mode or live-mode values before deployment.

### 2. Required Environment Variables

Add the following backend environment variables to local development, staging, and production secrets management:

- `STRIPE_SECRET_KEY`: server-side Stripe API key.
- `STRIPE_WEBHOOK_SECRET`: signing secret for the billing webhook endpoint.
- `STRIPE_COMMUNITY_PRICE_ID`: recurring monthly price ID for Community Member.
- `STRIPE_BUILDER_PRICE_ID`: recurring monthly price ID for Builder Member.
- `STRIPE_BILLING_PORTAL_RETURN_URL`: frontend account or membership page where Stripe returns users after portal actions.
- `STRIPE_CHECKOUT_SUCCESS_URL`: frontend success URL used by Checkout after payment completion.
- `STRIPE_CHECKOUT_CANCEL_URL`: frontend cancel URL used by Checkout when a user abandons payment.

Add the following frontend environment variable only if a browser-side Stripe.js flow is selected during implementation review:

- `VITE_STRIPE_PUBLISHABLE_KEY`: public Stripe publishable key.

Implementation checks:

1. Extend backend config validation so billing endpoints fail closed when required Stripe variables are missing.
2. Update `config/env.example` with placeholder values only.
3. Document which variables differ between test and live Stripe modes.

### 3. Subscription Database Model

Add a subscription persistence model before creating billing endpoints. The proposed model should support one active Stripe subscription per user at launch while preserving enough data for webhook reconciliation.

Proposed table: `subscriptions`

| Field | Purpose |
| --- | --- |
| `id` | Internal primary key. |
| `user_id` | Foreign key to the local user. |
| `stripe_customer_id` | Stripe customer attached to the local user. |
| `stripe_subscription_id` | Stripe subscription ID; unique when present. |
| `stripe_price_id` | Price ID that maps to the membership tier. |
| `membership_role` | `community_member` or `builder_member`. |
| `status` | Stripe subscription status such as `active`, `trialing`, `past_due`, `canceled`, or `unpaid`. |
| `current_period_end` | Subscription period end timestamp. |
| `cancel_at_period_end` | Whether the subscription is scheduled to cancel at period end. |
| `latest_invoice_id` | Latest Stripe invoice ID for support/debugging. |
| `last_event_id` | Last processed Stripe webhook event ID for idempotency. |
| `created_at` / `updated_at` | Audit timestamps. |

Implementation checks:

1. Add a migration or schema initialization path for `subscriptions`.
2. Add indexes for `user_id`, `stripe_customer_id`, and `stripe_subscription_id`.
3. Add a helper that maps `STRIPE_COMMUNITY_PRICE_ID` to `community_member` and `STRIPE_BUILDER_PRICE_ID` to `builder_member`.
4. Ensure unknown price IDs are rejected and logged without granting paid roles.

### 4. Checkout Session Endpoint

Create a backend endpoint after the model is approved:

- `POST /billing/create-checkout-session`

Expected behavior:

1. Require an authenticated user.
2. Accept a requested tier value of `community_member` or `builder_member`.
3. Resolve the requested tier to the configured Stripe price ID.
4. Create or reuse a Stripe customer for the authenticated user.
5. Create a Stripe Checkout subscription session with the selected recurring price.
6. Include local `user_id` and requested `membership_role` in Checkout metadata.
7. Return only the Checkout URL or session ID needed by the frontend.
8. Do not grant paid roles from this endpoint; roles are granted only after verified Stripe events.

### 5. Webhook Endpoint

Create a backend endpoint after the model is approved:

- `POST /billing/webhook`

Expected behavior:

1. Read the raw request body and verify the Stripe signature using `STRIPE_WEBHOOK_SECRET`.
2. Reject unsigned or invalid webhook payloads.
3. Process webhook events idempotently using Stripe event IDs.
4. Persist subscription state from Stripe before syncing roles.
5. Handle at minimum:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
6. Log unhandled Stripe event types without failing the endpoint.
7. Return a 2xx response only after the event is safely verified and persisted.

### 6. Billing Portal Endpoint

Create a backend endpoint after the model is approved:

- `POST /billing/create-portal-session`

Expected behavior:

1. Require an authenticated user.
2. Look up the user's Stripe customer ID from subscription persistence or user billing metadata.
3. Reject the request if no Stripe customer exists for the user.
4. Create a Stripe Billing Portal session with `STRIPE_BILLING_PORTAL_RETURN_URL`.
5. Return the portal URL to the frontend.
6. Let webhooks, not the portal endpoint response, apply subscription and role changes.

### 7. Success And Cancel Pages

Add frontend pages after the backend endpoints are approved:

- Success page route: `/membership/success`
- Cancel page route: `/membership/cancel`

Success page behavior:

1. Tell the user payment was received or is being finalized.
2. Refresh authenticated user/RBAC state after redirect.
3. Explain that membership access may take a few seconds while Stripe webhooks finish.
4. Link back to the member dashboard or account page.

Cancel page behavior:

1. Tell the user checkout was canceled and no subscription was activated.
2. Offer links to retry Community or Builder checkout.
3. Do not alter local roles or subscription state.

### 8. Role Sync Behavior

Paid role changes must be driven by verified Stripe subscription state, not by frontend redirects or checkout endpoint responses.

Approved role grants:

- Paid Community subscription with an `active` or approved paid-equivalent status grants `community_member`.
- Paid Builder subscription with an `active` or approved paid-equivalent status grants `builder_member`.
- Builder membership should include baseline Community permissions through RBAC role-permission configuration, not by duplicating unrelated user state.

Cancellation and payment-failure behavior to review before implementation:

1. `cancel_at_period_end = true`: keep the paid role until `current_period_end`, then downgrade if no active replacement subscription exists.
2. `canceled`: remove the paid role after the final verified Stripe state is persisted, unless a reviewed grace-period policy says otherwise.
3. `past_due`: do not immediately remove the paid role until the team approves a grace-period policy; mark the subscription as payment-risk and document the user's access state.
4. `unpaid` or expired grace period: downgrade from `builder_member` or `community_member` to the approved non-paid baseline role.
5. Unknown or mismatched Stripe price ID: persist diagnostic state if useful, but do not grant paid access.
6. Manual admin overrides, if needed, must be documented separately so they do not conflict with Stripe as the paid-membership source of truth.

## Review Checklist Before Writing Stripe Code

- [ ] Product names, prices, currency, and lookup keys are approved.
- [ ] Environment variable names are approved for local, staging, and production.
- [ ] Subscription model fields and indexes are approved.
- [ ] Checkout endpoint request/response contract is approved.
- [ ] Webhook event list and idempotency behavior are approved.
- [ ] Billing portal behavior is approved.
- [ ] Success/cancel routes and user messages are approved.
- [ ] Cancellation, `past_due`, grace-period, and downgrade policy is approved.
