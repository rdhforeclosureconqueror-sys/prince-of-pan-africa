from __future__ import annotations

import os
from urllib.parse import urljoin

try:
    import stripe
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal test envs
    stripe = None
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_auth
from app.models import StripeWebhookEvent, Subscription, User
from app.services.billing import (
    create_pending_subscription_checkout,
    has_active_paid_subscription,
    latest_subscription_for_user,
    normalize_subscription_plan,
    price_id_for_plan,
    stripe_checkout_enabled,
    stripe_client_ready,
    stripe_is_configured,
    stripe_webhook_is_configured,
    sync_subscription_user_role,
    tier_for_price_id,
    tier_for_subscription_plan,
    upsert_subscription_from_stripe,
)

router = APIRouter(prefix="/billing", tags=["Billing"])


class CheckoutPayload(BaseModel):
    plan: str


def _frontend_url(path: str) -> str:
    base = os.getenv("FRONTEND_URL", "https://prince-of-pan-africa.onrender.com").strip().rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def _safe_user_id(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@router.get("/config")
def get_billing_config():
    return {
        "ok": True,
        "stripe_configured": stripe_is_configured(),
        "webhook_configured": stripe_webhook_is_configured(),
        "checkout_enabled": stripe_checkout_enabled(),
        "live_checkout_active": stripe_checkout_enabled(),
        "plans": ["community", "builder"],
    }


@router.get("/status")
def get_billing_status(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    subscription = latest_subscription_for_user(db, current_user.id)
    active = bool(subscription and has_active_paid_subscription(db, current_user.id, subscription.tier))
    return {
        "ok": True,
        "active": active,
        "tier": subscription.tier if subscription else None,
        "status": subscription.status if subscription else None,
        "current_period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
    }


@router.post("/checkout")
def create_checkout_session(
    payload: CheckoutPayload,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    plan = normalize_subscription_plan(payload.plan)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown membership plan")

    price_id = price_id_for_plan(plan)
    if not price_id or tier_for_price_id(price_id) != tier_for_subscription_plan(plan):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Membership price is not configured")

    if not stripe_client_ready() or stripe is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe checkout is not enabled")

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()

    existing_subscription = latest_subscription_for_user(db, current_user.id)
    customer_id = existing_subscription.stripe_customer_id if existing_subscription else None

    try:
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)},
            )
            customer_id = customer.id

        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            customer=customer_id,
            client_reference_id=str(current_user.id),
            metadata={"user_id": str(current_user.id), "plan": plan},
            subscription_data={"metadata": {"user_id": str(current_user.id), "plan": plan, "price_id": price_id}},
            success_url=_frontend_url("/billing/success?session_id={CHECKOUT_SESSION_ID}"),
            cancel_url=_frontend_url("/billing/cancel"),
        )
        create_pending_subscription_checkout(
            db,
            user_id=current_user.id,
            stripe_customer_id=customer_id,
            stripe_price_id=price_id,
            plan=plan,
            checkout_session_id=checkout_session.id,
        )
        db.commit()
    except stripe.StripeError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to create Stripe checkout session") from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Membership price is not configured") from exc

    return {"ok": True, "checkout_url": checkout_session.url, "session_id": checkout_session.id}


@router.post("/portal")
def create_billing_portal_session(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    subscription = latest_subscription_for_user(db, current_user.id)
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stripe customer not found")

    if not stripe_client_ready() or stripe is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe billing portal is not enabled")

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=_frontend_url("/dashboard"),
        )
    except stripe.StripeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to create billing portal session") from exc

    return {"ok": True, "portal_url": portal_session.url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not stripe_signature or not secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe webhook signature")

    payload = await request.body()
    if stripe is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe webhook support is not installed")

    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, secret)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe webhook signature") from exc

    event_id = event.get("id")
    event_type = event.get("type")
    if not event_id or not event_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe webhook event")

    if db.query(StripeWebhookEvent).filter_by(stripe_event_id=event_id).first():
        return {"ok": True, "received": True, "duplicate": True}

    data_object = event.get("data", {}).get("object", {})

    try:
        db.add(StripeWebhookEvent(stripe_event_id=event_id, event_type=event_type))

        if event_type == "checkout.session.completed":
            subscription_id = data_object.get("subscription")
            if subscription_id:
                stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
                subscription = stripe.Subscription.retrieve(subscription_id)
                record = upsert_subscription_from_stripe(db, subscription, user_id=_safe_user_id(data_object.get("client_reference_id")))
                sync_subscription_user_role(db, record)
        elif event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
            record = upsert_subscription_from_stripe(db, data_object)
            sync_subscription_user_role(db, record)
        elif event_type in {"invoice.payment_failed", "invoice.payment_action_required"}:
            subscription_id = data_object.get("subscription")
            if subscription_id:
                record = db.query(Subscription).filter_by(stripe_subscription_id=subscription_id).first()
                if record:
                    record.status = "past_due"
                    db.flush()
                    sync_subscription_user_role(db, record)

        db.commit()
    except (ValueError, stripe.StripeError) as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook event could not be processed") from exc

    return {"ok": True, "received": True}
