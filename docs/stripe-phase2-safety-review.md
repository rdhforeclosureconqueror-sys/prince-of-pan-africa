# Stripe Phase 2 Safety Review

Date: 2026-06-15
Reviewed commit: ade2e34 / current safety-fix branch

## Current safety status

1. **Checkout remains disabled.** `/billing/checkout` returns `501 Not Implemented` and does not call Stripe or create Checkout sessions. `stripe_checkout_enabled()` also requires both `ENABLE_STRIPE_CHECKOUT=true` and a non-placeholder Stripe secret key.
2. **Webhook processing remains non-functional.** `/billing/webhook` returns `501 Not Implemented` and does not parse Stripe events, update subscriptions, or mutate roles.
3. **No credentials are hardcoded.** Stripe keys and price IDs are empty placeholders in `config/env.example`; no secret or live key values are committed.
4. **Missing config fails safely.** Empty or placeholder `STRIPE_SECRET_KEY` values make `stripe_is_configured()` false, and checkout cannot become enabled without a valid-looking Stripe secret key.
5. **Subscriptions do not grant access by themselves.** The `Subscription` model stores billing state only; no auth dependency, route guard, seed, or webhook code reads it to grant permissions.
6. **Tier mapping is intentionally narrow.** Public plan names map only `community -> community_member` and `builder -> builder_member`; unknown values return `None`.
7. **Unknown prices fail closed.** `tier_for_price_id()` returns a tier only for configured `STRIPE_COMMUNITY_PRICE_ID` or `STRIPE_BUILDER_PRICE_ID`; unknown or missing price IDs return `None`.
8. **Return pages are not proof of payment.** `/billing/success` says the billing return is unverified and must be checked against backend subscription state before showing active access.

## Must review before enabling live checkout

- Confirm Stripe account mode and use test mode first; do not deploy with `sk_live_` until test-mode checkout, webhook verification, and rollback are proven.
- Confirm exact configured price IDs for Community and Builder plans, including currency, billing interval, trial behavior, and product names in Stripe.
- Add backend Checkout session creation with authenticated user binding, allowlisted tier/price selection only, server-generated success/cancel URLs, and no client-supplied price IDs.
- Add webhook signature verification using `STRIPE_WEBHOOK_SECRET` before reading any event payload.
- Add idempotency handling for webhook events and subscription updates.
- Define subscription status transitions that grant access only for explicitly active/paid states, never for pending, incomplete, canceled, unpaid, or unknown statuses.
- Review RBAC migration path before any Stripe event mutates user roles; role updates must be explicit, logged, reversible, and covered by tests.
- Add tests for checkout disabled/enabled config gates, unknown price IDs, webhook signature failure, ignored event types, idempotency, and non-active subscription statuses.
- Add operational logging that avoids secrets and avoids full raw Stripe payload dumps.
- Confirm environment variables in deployment are set outside git and that secret scanning passes before enabling live checkout.
