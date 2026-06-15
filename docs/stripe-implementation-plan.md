# Stripe Implementation Plan

Status: Planning only. Stripe is not implemented in this phase.

## Membership Products

Create two recurring monthly Stripe prices:

- Community Member — `$10/month`
- Builder Member — `$25/month`

## Required Environment Variables

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_COMMUNITY_PRICE_ID`
- `STRIPE_BUILDER_PRICE_ID`
- `VITE_STRIPE_PUBLISHABLE_KEY` if Stripe.js is used on the frontend

## Backend Endpoints To Build Later

- `POST /billing/create-checkout-session`
- `POST /billing/create-portal-session`
- `POST /billing/webhook`

## Webhook Events To Handle Later

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

## Subscription State To Persist Later

- Stripe customer ID
- Stripe subscription ID
- Stripe price ID
- Membership type: `community_member` or `builder_member`
- Subscription status
- Current period end
- Cancel-at-period-end flag

## Role Sync Rules

- Active Community subscription assigns `community_member`.
- Active Builder subscription assigns `builder_member`.
- Builder includes all Community permissions.
- Canceled or failed subscriptions should downgrade or restrict paid permissions according to the final launch grace-period policy.

## Explicit Non-Goals For Current Phase

- No Stripe SDK installation.
- No checkout session creation.
- No webhook route.
- No production price IDs.
- No payment-dependent role changes.
