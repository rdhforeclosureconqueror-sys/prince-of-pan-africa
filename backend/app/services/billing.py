"""Safe billing helpers for Stripe foundation work.

This module intentionally does not create Checkout sessions, process webhooks,
or mutate user roles from Stripe events. It only centralizes safe configuration
checks and deterministic, fail-closed tier mapping for future phases.
"""

from __future__ import annotations

import os

COMMUNITY_PLAN = "community"
BUILDER_PLAN = "builder"
COMMUNITY_TIER = "community_member"
BUILDER_TIER = "builder_member"
KNOWN_SUBSCRIPTION_PLANS = {COMMUNITY_PLAN, BUILDER_PLAN}
KNOWN_SUBSCRIPTION_TIERS = {COMMUNITY_TIER, BUILDER_TIER}


def stripe_is_configured() -> bool:
    """Return True only when a secret key placeholder has been replaced."""
    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not key or key.startswith("replace-") or key.startswith("sk_test_placeholder"):
        return False
    return key.startswith(("sk_test_", "sk_live_"))


def stripe_checkout_enabled() -> bool:
    """Live checkout remains disabled unless explicitly enabled and configured."""
    enabled = os.getenv("ENABLE_STRIPE_CHECKOUT", "false").strip().lower() in {"1", "true", "yes", "on"}
    return enabled and stripe_is_configured()


def normalize_subscription_plan(value: str | None) -> str | None:
    """Normalize public plan names; unknown values fail closed as None."""
    normalized = (value or "").strip().lower().replace("-", "_")
    if normalized in {COMMUNITY_PLAN, COMMUNITY_TIER}:
        return COMMUNITY_PLAN
    if normalized in {BUILDER_PLAN, BUILDER_TIER}:
        return BUILDER_PLAN
    return None


def tier_for_subscription_plan(plan: str | None) -> str | None:
    """Map only known plans to internal membership tiers; unknowns fail closed."""
    normalized = normalize_subscription_plan(plan)
    if normalized == COMMUNITY_PLAN:
        return COMMUNITY_TIER
    if normalized == BUILDER_PLAN:
        return BUILDER_TIER
    return None


def role_for_subscription_tier(tier: str | None) -> str | None:
    """Map only known billing tiers to membership role names without applying changes."""
    normalized = (tier or "").strip().lower().replace("-", "_")
    if normalized == COMMUNITY_TIER:
        return COMMUNITY_TIER
    if normalized == BUILDER_TIER:
        return BUILDER_TIER
    return None


def tier_for_price_id(price_id: str | None) -> str | None:
    """Resolve configured Stripe price IDs to tiers; unknown or missing IDs fail closed."""
    normalized_price_id = (price_id or "").strip()
    if not normalized_price_id:
        return None

    configured_prices = {
        (os.getenv("STRIPE_COMMUNITY_PRICE_ID", "").strip()): COMMUNITY_TIER,
        (os.getenv("STRIPE_BUILDER_PRICE_ID", "").strip()): BUILDER_TIER,
    }
    configured_prices.pop("", None)
    return configured_prices.get(normalized_price_id)
