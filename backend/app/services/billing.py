"""Stripe billing helpers for live membership checkout and role sync."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models import Subscription, User

COMMUNITY_PLAN = "community"
BUILDER_PLAN = "builder"
COMMUNITY_TIER = "community_member"
BUILDER_TIER = "builder_member"
KNOWN_SUBSCRIPTION_PLANS = {COMMUNITY_PLAN, BUILDER_PLAN}
KNOWN_SUBSCRIPTION_TIERS = {COMMUNITY_TIER, BUILDER_TIER}
ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}
PAID_ACCESS_TIERS = {COMMUNITY_TIER, BUILDER_TIER}


def stripe_is_configured() -> bool:
    """Return True only when a secret key placeholder has been replaced."""
    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not key or key.startswith("replace-") or key.startswith("sk_test_placeholder"):
        return False
    return key.startswith(("sk_test_", "sk_live_"))


def stripe_webhook_is_configured() -> bool:
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    return bool(secret and not secret.startswith("replace-") and not secret.startswith("whsec_placeholder"))


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


def price_id_for_plan(plan: str | None) -> str | None:
    normalized = normalize_subscription_plan(plan)
    if normalized == COMMUNITY_PLAN:
        return os.getenv("STRIPE_COMMUNITY_PRICE_ID", "").strip() or None
    if normalized == BUILDER_PLAN:
        return os.getenv("STRIPE_BUILDER_PRICE_ID", "").strip() or None
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


def stripe_client_ready() -> bool:
    if not stripe_checkout_enabled():
        return False
    return True


def unix_to_datetime(value: int | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).replace(tzinfo=None)


def extract_subscription_price_id(subscription: dict[str, Any]) -> str | None:
    items = subscription.get("items", {}).get("data", [])
    if not items:
        return None
    price = items[0].get("price") or {}
    return price.get("id")


def create_pending_subscription_checkout(
    db: "Session",
    *,
    user_id: int,
    stripe_customer_id: str,
    stripe_price_id: str,
    plan: str,
    checkout_session_id: str | None = None,
) -> "Subscription":
    from app.models import Subscription

    tier = tier_for_subscription_plan(plan)
    if tier is None or tier_for_price_id(stripe_price_id) != tier:
        raise ValueError("Unknown Stripe checkout price ID")

    record = Subscription(
        user_id=user_id,
        stripe_customer_id=stripe_customer_id,
        stripe_price_id=stripe_price_id,
        tier=tier,
        status="checkout_pending",
        raw_metadata={"checkout_session_id": checkout_session_id, "plan": plan},
    )
    db.add(record)
    db.flush()
    return record

def upsert_subscription_from_stripe(db: "Session", subscription: dict[str, Any], user_id: int | None = None) -> "Subscription":
    from app.models import Subscription
    price_id = extract_subscription_price_id(subscription)
    tier = tier_for_price_id(price_id)
    if tier is None:
        raise ValueError("Unknown Stripe price ID")

    stripe_subscription_id = subscription.get("id")
    if not stripe_subscription_id:
        raise ValueError("Missing Stripe subscription ID")

    customer_id = subscription.get("customer")
    metadata = dict(subscription.get("metadata") or {})
    resolved_user_id = user_id or _safe_int(metadata.get("user_id"))
    if resolved_user_id is None and customer_id:
        existing_for_customer = latest_subscription_for_customer(db, customer_id)
        if existing_for_customer:
            resolved_user_id = existing_for_customer.user_id

    record = db.query(Subscription).filter(Subscription.stripe_subscription_id == stripe_subscription_id).first()
    if record is None:
        record = Subscription(stripe_subscription_id=stripe_subscription_id)
        db.add(record)

    record.user_id = resolved_user_id
    record.stripe_customer_id = customer_id
    record.stripe_price_id = price_id
    record.tier = tier
    record.status = (subscription.get("status") or "unknown").strip().lower() or "unknown"
    record.current_period_end = unix_to_datetime(subscription.get("current_period_end"))
    record.raw_metadata = metadata
    db.flush()
    return record


def latest_subscription_for_customer(db: "Session", customer_id: str) -> "Subscription | None":
    from app.models import Subscription
    return (
        db.query(Subscription)
        .filter(Subscription.stripe_customer_id == customer_id)
        .order_by(Subscription.updated_at.desc(), Subscription.id.desc())
        .first()
    )


def latest_subscription_for_user(db: "Session", user_id: int) -> "Subscription | None":
    from app.models import Subscription
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .order_by(Subscription.updated_at.desc(), Subscription.id.desc())
        .first()
    )


def has_active_paid_subscription(db: "Session", user_id: int, tier: str | None = None) -> bool:
    from app.models import Subscription
    query = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES),
        Subscription.tier.in_(PAID_ACCESS_TIERS),
    )
    if tier:
        query = query.filter(Subscription.tier == tier)
    return db.query(query.exists()).scalar()


def sync_paid_roles_for_user(db: "Session", user: "User") -> None:
    """Grant paid roles only after active subscription rows already exist."""
    from app.models import Role, Subscription, UserRole
    active_tiers = {
        tier
        for (tier,) in db.query(Subscription.tier)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES),
            Subscription.tier.in_(PAID_ACCESS_TIERS),
        )
        .all()
    }

    for tier in PAID_ACCESS_TIERS:
        role = db.query(Role).filter(Role.name == tier).first()
        if role is None:
            role = Role(name=tier)
            db.add(role)
            db.flush()
        existing = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).first()
        if tier in active_tiers and existing is None:
            db.add(UserRole(user_id=user.id, role_id=role.id))
        if tier not in active_tiers and existing is not None:
            db.delete(existing)

    if BUILDER_TIER in active_tiers:
        user.role = BUILDER_TIER
    elif COMMUNITY_TIER in active_tiers:
        user.role = COMMUNITY_TIER
    elif user.role in PAID_ACCESS_TIERS:
        user.role = "member"
    db.flush()


def sync_subscription_user_role(db: "Session", subscription: "Subscription") -> None:
    from app.models import User
    if subscription.user_id is None:
        return
    user = db.query(User).filter(User.id == subscription.user_id).first()
    if user is None:
        return
    sync_paid_roles_for_user(db, user)


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
