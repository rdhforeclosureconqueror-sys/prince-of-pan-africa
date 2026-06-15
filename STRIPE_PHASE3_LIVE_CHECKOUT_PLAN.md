# Stripe Phase 3 Live Checkout Implementation Plan

This is a planning-only document. Do not write Phase 3 live checkout code until this plan receives explicit review approval.

## 1. Exact environment variables needed

Set these values in every environment before enabling live checkout. Keep `ENABLE_STRIPE_CHECKOUT=false` until all dashboard, webhook, database, and test steps pass.

| Variable | Required value | Purpose | Notes |
| --- | --- | --- | --- |
| `ENABLE_STRIPE_CHECKOUT` | `false` during implementation and testing; `true` only after approval | Feature gate for live checkout, webhooks, and billing portal creation | Existing foundation must continue to fail closed when this is false or when Stripe credentials are missing. |
| `STRIPE_SECRET_KEY` | Stripe secret API key for the target mode, such as `sk_test_...` first and later `sk_live_...` | Server-side Stripe API authentication | Never expose to frontend. The existing `stripe_is_configured()` helper already rejects empty placeholders. |
| `STRIPE_WEBHOOK_SECRET` | Stripe endpoint signing secret, such as `whsec_...` | Verifies webhook authenticity | Must come from the exact webhook endpoint configured for the backend environment. |
| `STRIPE_COMMUNITY_PRICE_ID` | Stripe recurring Price ID for Community, such as `price_...` | Maps the Community checkout line item to `community_member` | Must match the active recurring Price, not the Product ID. |
| `STRIPE_BUILDER_PRICE_ID` | Stripe recurring Price ID for Builder, such as `price_...` | Maps the Builder checkout line item to `builder_member` | Must match the active recurring Price, not the Product ID. |
| `APP_BASE_URL` | Public backend origin, for example `https://api.simbawaujamaa.com` | Backend absolute URL generation and webhook/portal documentation | Add this as the canonical backend URL for Phase 3. If legacy `BACKEND_URL` remains, `APP_BASE_URL` should take precedence. |
| `FRONTEND_BASE_URL` | Public frontend origin, for example `https://simbawaujamaa.com` | Checkout `success_url`, `cancel_url`, and billing portal `return_url` | Needed because Stripe redirects users to frontend pages. If legacy `FRONTEND_URL` remains, `FRONTEND_BASE_URL` should take precedence. |

Recommended compatibility rule during implementation: read `FRONTEND_BASE_URL` first and fall back to existing `FRONTEND_URL`; read `APP_BASE_URL` first and fall back to existing `BACKEND_URL` or `BASE_URL` only for backward compatibility.

## 2. Checkout endpoint implementation steps

1. Keep the existing `/billing/config` safe status endpoint, but update it to report whether Phase 3 is fully configured without exposing secrets.
2. Replace the current `/billing/checkout` placeholder with an authenticated endpoint that requires `require_auth`.
3. Accept a small validated payload containing only the requested tier or plan: `community`, `community_member`, `builder`, or `builder_member`.
4. Normalize the requested plan with the existing billing helper and reject unknown tiers with `400`.
5. Resolve the tier to the configured Price ID: `community_member -> STRIPE_COMMUNITY_PRICE_ID`, `builder_member -> STRIPE_BUILDER_PRICE_ID`.
6. Fail closed with `503` when `ENABLE_STRIPE_CHECKOUT` is not enabled, Stripe is not configured, required Price IDs are missing, or `FRONTEND_BASE_URL` is missing.
7. Look up the authenticated user by session, then find an existing active Stripe customer binding in local subscriptions by `user_id`.
8. If no Stripe customer exists, create one using the authenticated user's email and local `user_id` metadata, then persist `stripe_customer_id` on a local subscription/customer binding before creating Checkout.
9. Create a Stripe Checkout Session in `subscription` mode with exactly one line item and the resolved Price ID.
10. Set Checkout Session metadata and subscription metadata with local `user_id`, normalized tier, and requested Price ID.
11. Set `client_reference_id` to the local user ID for traceability, but do not rely on it as the only source of truth.
12. Use `success_url = {FRONTEND_BASE_URL}/billing/success?session_id={CHECKOUT_SESSION_ID}` and `cancel_url = {FRONTEND_BASE_URL}/billing/cancel`.
13. Return only the Checkout Session URL and a short session identifier to the frontend; never return Stripe secrets or raw customer objects.
14. Add idempotency keys for customer creation and checkout creation based on user ID, tier, and a request nonce when appropriate.
15. Record a pending local `Subscription` row before redirect, with `status="checkout_pending"`, the requested tier, `stripe_customer_id`, `stripe_price_id`, and raw metadata that is safe to store.

## 3. Webhook implementation steps

1. Keep `/billing/webhook` public at the HTTP layer but verify the raw body with `STRIPE_WEBHOOK_SECRET` before parsing or mutating anything.
2. Return `503` when Stripe checkout is disabled, and `400` for invalid signatures.
3. Process only allowlisted events in Phase 3:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Ignore unknown event types with a `200` response after logging the type.
5. Add webhook idempotency using Stripe `event.id`; if no event table exists yet, add one before implementation so duplicate deliveries do not reapply role changes.
6. For `checkout.session.completed`, verify `mode=subscription`, extract `customer`, `subscription`, metadata `user_id`, and the selected Price ID, then upsert the local subscription.
7. For subscription events, retrieve the subscription item Price ID, map it through `tier_for_price_id()`, and fail closed if the Price ID is unknown.
8. For invoice events, use the invoice subscription/customer IDs to refresh local subscription status, but do not grant new access from invoice data alone unless the subscription status is active/trialing.
9. Persist Stripe subscription ID, customer ID, price ID, normalized tier, status, current period end, and minimal raw event metadata.
10. Apply role changes only after local subscription state has been successfully committed or inside the same transaction.
11. Log enough context for support: event ID, event type, Stripe customer ID, Stripe subscription ID, local user ID, old status, new status, and resulting role action.

## 4. Billing portal implementation steps

1. Add an authenticated `POST /billing/portal` endpoint after checkout is approved.
2. Require an authenticated local user and a known `stripe_customer_id` bound to that user.
3. Fail closed with `404` or `409` if the user has no Stripe customer or has an ambiguous customer binding.
4. Create a Stripe Billing Portal Session with that customer and `return_url = {FRONTEND_BASE_URL}/membership` or a dedicated account billing page.
5. Return only the portal session URL to the frontend.
6. Do not allow the frontend to submit a customer ID; derive it only from the authenticated user's local subscription records.
7. Ensure portal actions are reflected only through verified webhooks, not from portal redirects.

## 5. How authenticated users are matched to Stripe customers

1. The backend session identifies the local `User` through the existing auth dependency.
2. The local user is matched to Stripe through `Subscription.user_id` and `Subscription.stripe_customer_id`.
3. Checkout creates or reuses exactly one Stripe customer for that local user.
4. Stripe Customer metadata should include local `user_id` and email at creation time.
5. Stripe Subscription metadata should include local `user_id`, normalized tier, and Price ID.
6. Webhooks should prefer verified subscription/customer IDs already stored locally, then validate metadata `user_id` only as a secondary reconciliation signal.
7. Email is useful for support and reconciliation, but it must not be the primary identity key because emails can change and are not proof of account ownership.

## 6. How new users without accounts should be handled

Phase 3 should require account creation before checkout.

1. Unauthenticated clicks on membership checkout should redirect to login/signup with the intended tier preserved in a safe query parameter or local UI state.
2. After signup/login, the user can retry checkout as an authenticated user.
3. Do not create anonymous subscriptions or grant access from an email-only Stripe Checkout flow in Phase 3.
4. If a Stripe payment is discovered without a matching user during manual reconciliation, do not auto-create a privileged account. Put it in a support/reconciliation state until the user proves account ownership.
5. A future guest-checkout phase may be designed separately, but it must include verified account claim flows before access is granted.

## 7. How subscription status updates map to roles

Use the existing safe tier names and role names:

| Stripe subscription status | Local subscription status | Role action |
| --- | --- | --- |
| `active` | `active` | Grant mapped role: `community_member` or `builder_member`. |
| `trialing` | `trialing` | Grant mapped role if trials are intentionally enabled in Stripe. If trials are not approved, configure no trials in Stripe. |
| `canceled` | `canceled` | Remove paid tier role and keep baseline `member`. |
| `incomplete` | `incomplete` | Do not grant paid tier role. |
| `incomplete_expired` | `incomplete_expired` | Do not grant paid tier role. |
| `past_due` | `past_due` | Recommended Phase 3 policy: keep existing paid tier during Stripe retry/grace period, mark account as billing attention required. |
| `unpaid` | `unpaid` | Remove paid tier role and keep baseline `member`. |
| `paused` | `paused` | Remove paid tier role unless an approved pause-access policy says otherwise. |

If a user changes from Builder to Community, remove `builder_member` and grant `community_member`. If a user changes from Community to Builder, grant `builder_member` and remove `community_member` unless product requirements explicitly allow both roles.

## 8. How cancellations, `past_due`, `incomplete`, and `unpaid` statuses are handled

1. `canceled`: immediately record the cancellation status from Stripe. Remove paid tier access and leave the user with baseline `member` access.
2. `past_due`: record the status and current period end. Keep the paid role during Stripe's retry window for Phase 3, surface a billing warning in the frontend, and rely on later `active`, `unpaid`, or `canceled` webhooks to resolve access.
3. `incomplete`: record the status but do not grant paid access. The success page must not claim access until backend state is active or trialing.
4. `incomplete_expired`: record the status, do not grant access, and prompt the user to restart checkout.
5. `unpaid`: record the status and remove paid access until Stripe reports a paid active/trialing subscription again.
6. Unknown statuses: store the status for diagnostics but fail closed by removing paid tier roles unless explicitly allowlisted later.

## 9. How success/cancel pages verify backend subscription state

1. The success page must read `session_id` from the query string and call an authenticated backend verification endpoint such as `GET /billing/checkout-session/{session_id}` or `GET /billing/subscription/status`.
2. The backend must confirm the session belongs to the authenticated user before returning any state.
3. The backend should retrieve the Checkout Session from Stripe when needed, but access should be based on the local subscription state after webhook processing.
4. The success page should show a pending state while webhooks are still processing, then poll briefly or provide a refresh action.
5. The success page may show active access only when the backend reports a local subscription status of `active` or approved `trialing` and the mapped role is present.
6. The cancel page should not verify payment. It should state checkout was canceled and offer retry/navigation.
7. Neither success nor cancel pages should grant frontend-only access based on query parameters.

## 10. Manual Stripe dashboard steps still needed before implementation

1. Create or confirm the Community Product and recurring Price in Stripe test mode.
2. Create or confirm the Builder Product and recurring Price in Stripe test mode.
3. Copy the recurring Price IDs into `STRIPE_COMMUNITY_PRICE_ID` and `STRIPE_BUILDER_PRICE_ID` for the test environment.
4. Configure the customer portal settings in Stripe, including allowed subscription updates/cancellations and return URL behavior.
5. Create a test-mode webhook endpoint pointing to `{APP_BASE_URL}/billing/webhook`.
6. Subscribe that webhook endpoint to the Phase 3 allowlisted events.
7. Copy the webhook signing secret into `STRIPE_WEBHOOK_SECRET`.
8. Confirm the frontend success and cancel routes exist and are deployed under `FRONTEND_BASE_URL`.
9. Decide whether trials are allowed. If not, ensure Stripe Prices/Checkout settings do not create trials.
10. Decide the grace-period policy for `past_due` and confirm it matches Stripe retry settings.
11. Repeat the same setup in live mode only after test mode passes and review approval is granted.
12. Keep `ENABLE_STRIPE_CHECKOUT=false` in live production until final activation approval.

## 11. Test plan before live activation

1. Unit-test configuration fail-closed behavior for missing keys, placeholder keys, disabled checkout, and missing base URLs.
2. Unit-test tier and Price ID mapping for Community, Builder, unknown Price IDs, and missing Price IDs.
3. Unit-test checkout endpoint auth requirements, invalid tier rejection, disabled checkout rejection, and valid Checkout Session creation with mocked Stripe APIs.
4. Unit-test customer reuse so existing authenticated users do not get duplicate Stripe customers.
5. Unit-test portal endpoint auth requirements, missing customer handling, and valid portal session creation with mocked Stripe APIs.
6. Unit-test webhook signature verification with valid and invalid signatures.
7. Unit-test webhook idempotency with duplicate Stripe event IDs.
8. Unit-test subscription status mapping and role updates for `active`, `trialing`, `canceled`, `past_due`, `incomplete`, `incomplete_expired`, `unpaid`, and unknown statuses.
9. Integration-test the full test-mode checkout flow with Stripe test cards: successful payment, canceled checkout, failed payment, subscription cancellation, plan upgrade, and plan downgrade.
10. Verify success page behavior when webhook processing is delayed: pending first, active only after backend state changes.
11. Verify cancel page does not grant access and allows retry.
12. Verify unauthenticated users are sent through signup/login before checkout and that the chosen tier is preserved.
13. Verify production environment has all required variables set but still keeps `ENABLE_STRIPE_CHECKOUT=false` until final approval.
14. Run regression tests for existing auth, RBAC, member dashboard, and billing foundation.
15. Perform a final manual dashboard audit in Stripe test mode before switching any live settings.

## Review gate

Phase 3 code must not be written until this plan is reviewed and explicitly approved. After approval, implementation should be split into small commits: configuration and tests first, checkout endpoint second, webhook processing third, portal endpoint fourth, and frontend status verification last.
