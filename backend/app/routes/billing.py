from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.billing import stripe_checkout_enabled, stripe_is_configured

router = APIRouter(prefix="/billing", tags=["Billing"])


class CheckoutPlaceholderPayload(BaseModel):
    tier: str = "community_member"


@router.get("/config")
def get_billing_config():
    return {
        "ok": True,
        "stripe_configured": stripe_is_configured(),
        "checkout_enabled": stripe_checkout_enabled(),
        "live_checkout_active": False,
    }


@router.post("/checkout")
def create_checkout_placeholder(payload: CheckoutPlaceholderPayload):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Stripe Checkout is not active yet. "
            f"Received safe placeholder request for tier '{payload.tier}'."
        ),
    )


@router.post("/webhook")
def stripe_webhook_placeholder():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Stripe webhook processing is intentionally disabled in this phase.",
    )
