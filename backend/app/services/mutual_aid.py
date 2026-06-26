from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.models import MutualAidAuditLog, MutualAidFund

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
