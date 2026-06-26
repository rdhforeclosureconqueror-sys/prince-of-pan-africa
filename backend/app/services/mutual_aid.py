from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.models import MutualAidAuditLog, MutualAidFund, MutualAidNotification

DEFAULT_MUTUAL_AID_FUND_NAME = "Simba Mutual Aid Society"
MUTUAL_AID_BUILDING_STATUS = "Building Toward Activation"
MUTUAL_AID_ACTIVATION_THRESHOLD = 20000
MUTUAL_AID_CURRENCY = "USD"


@dataclass(frozen=True)
class MutualAidAuditEntry:
    """Structured audit intent for future Mutual Aid actions; not wired to live flows."""

    entity_type: str
    action: str
    entity_id: int | None = None
    actor_user_id: int | None = None
    before: dict | None = None
    after: dict | None = None


def mutual_aid_feature_flags() -> dict[str, bool]:
    return {
        "ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION": settings.ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION,
        "MUTUAL_AID_REQUESTS_ENABLED": settings.MUTUAL_AID_REQUESTS_ENABLED,
        "ENABLE_MUTUAL_AID_REQUEST_INTAKE": settings.ENABLE_MUTUAL_AID_REQUEST_INTAKE,
        "MUTUAL_AID_REVIEW_ENABLED": settings.MUTUAL_AID_REVIEW_ENABLED,
        "ENABLE_MUTUAL_AID_REVIEW_WORKFLOW": settings.ENABLE_MUTUAL_AID_REVIEW_WORKFLOW,
        "MUTUAL_AID_DECISIONS_ENABLED": settings.MUTUAL_AID_DECISIONS_ENABLED,
        "ENABLE_MUTUAL_AID_PAYMENTS": settings.ENABLE_MUTUAL_AID_PAYMENTS,
        "MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED": settings.MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED,
        "MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED": settings.MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED,
        "MUTUAL_AID_NOTIFICATIONS_ENABLED": settings.MUTUAL_AID_NOTIFICATIONS_ENABLED,
        "MUTUAL_AID_APPEALS_ENABLED": settings.MUTUAL_AID_APPEALS_ENABLED,
        "MUTUAL_AID_PILOT_HARDENING_ENABLED": settings.MUTUAL_AID_PILOT_HARDENING_ENABLED,
    }


def seed_default_mutual_aid_fund(db: Session) -> MutualAidFund:
    fund = db.query(MutualAidFund).filter(MutualAidFund.name == DEFAULT_MUTUAL_AID_FUND_NAME).one_or_none()
    if fund is None:
        fund = MutualAidFund(
            name=DEFAULT_MUTUAL_AID_FUND_NAME,
            status=MUTUAL_AID_BUILDING_STATUS,
            activation_threshold=MUTUAL_AID_ACTIVATION_THRESHOLD,
            current_balance=0,
            available_balance=0,
            reserved_balance=0,
            currency=MUTUAL_AID_CURRENCY,
        )
        db.add(fund)
        db.commit()
        db.refresh(fund)
    return fund


def build_mutual_aid_audit_log(entry: MutualAidAuditEntry) -> MutualAidAuditLog:
    return MutualAidAuditLog(
        actor_user_id=entry.actor_user_id,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        action=entry.action,
        before=entry.before or {},
        after=entry.after or {},
    )


MUTUAL_AID_NOTIFICATION_COPY = {
    "request_submitted": ("Request submitted", "Your Mutual Aid request was submitted and is ready for review."),
    "admin_request_submitted": ("New Mutual Aid request", "A member submitted a Mutual Aid request for review."),
    "more_information_requested": ("More information requested", "The Mutual Aid review team requested more information for your request."),
    "admin_more_information_requested": ("More information requested", "A reviewer requested more information from the member."),
    "decision_recorded": ("Decision recorded", "A decision was recorded for your Mutual Aid request."),
    "admin_decision_recorded": ("Decision recorded", "A Mutual Aid decision was recorded by the review team."),
    "disbursement_record_created": ("Disbursement record created", "An internal disbursement tracking record was created for your approved Mutual Aid request."),
    "admin_disbursement_record_created": ("Disbursement record created", "An internal disbursement tracking record was created."),
    "receipt_needed": ("Receipt needed", "Please provide a receipt or confirmation for your Mutual Aid support record."),
    "admin_receipt_needed": ("Receipt needed", "A Mutual Aid disbursement record is marked as needing a receipt."),
    "appeal_window_reminder": ("Appeal window reminder", "This scaffold records that an appeal window reminder may be needed."),
    "appeal_submitted": ("Appeal submitted", "Your Mutual Aid appeal was submitted for governance review."),
    "admin_appeal_submitted": ("Appeal submitted", "A member submitted a Mutual Aid appeal for governance review."),
    "appeal_status_changed": ("Appeal status changed", "A governance reviewer updated your Mutual Aid appeal."),
    "admin_appeal_status_changed": ("Appeal status changed", "A Mutual Aid appeal was updated by governance review."),
}


def _notification_copy(event_type: str) -> tuple[str, str]:
    return MUTUAL_AID_NOTIFICATION_COPY.get(event_type, (event_type.replace("_", " ").title(), "Mutual Aid status update recorded."))


def record_mutual_aid_notification(
    db: Session,
    *,
    event_type: str,
    request_id: int | None,
    recipient_user_id: int | None,
    actor_user_id: int | None = None,
    audience: str = "member",
    disbursement_id: int | None = None,
    payload: dict | None = None,
    title: str | None = None,
    message: str | None = None,
) -> MutualAidNotification | None:
    """Persist an internal notification record only; never dispatch external email/SMS/push."""
    if not settings.MUTUAL_AID_NOTIFICATIONS_ENABLED:
        return None
    default_title, default_message = _notification_copy(event_type)
    row = MutualAidNotification(
        request_id=request_id,
        disbursement_id=disbursement_id,
        recipient_user_id=recipient_user_id,
        actor_user_id=actor_user_id,
        audience=audience,
        event_type=event_type,
        title=title or default_title,
        message=message or default_message,
        delivery_status="recorded_only",
        channels=[],
        payload=payload or {},
    )
    db.add(row)
    return row
