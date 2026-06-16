from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Activity
from app.services.participation import participation_summary, submit_activity

router = APIRouter(prefix="/participation", tags=["Participation"])


class ActivityPayload(BaseModel):
    activity_type: str = Field(min_length=1, max_length=128)
    source_module: str = Field(min_length=1, max_length=128)
    guest_session_id: str | None = Field(default=None, max_length=128)
    metadata: dict = Field(default_factory=dict)


def _serialize_activity(activity: Activity) -> dict:
    return {
        "id": activity.id,
        "activity_id": activity.id,
        "user_id": activity.user_id,
        "guest_session_id": activity.guest_session_id,
        "activity_type": activity.activity_type,
        "source_module": activity.source_module,
        "timestamp": activity.timestamp.isoformat() if activity.timestamp else None,
        "verification_status": activity.verification_status,
        "participation_points": activity.participation_points,
        "star_award": activity.star_award,
        "metadata": activity.metadata_,
    }


@router.post("/activity")
def create_participation_activity(
    payload: ActivityPayload,
    request: Request,
    x_guest_session_id: str | None = Header(default=None, alias="X-Guest-Session-Id"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guest_session_id = payload.guest_session_id or x_guest_session_id or request.cookies.get("simba_guest_session")
    activity = submit_activity(
        db,
        user=current_user,
        guest_session_id=guest_session_id,
        activity_type_name=payload.activity_type,
        source_module=payload.source_module,
        metadata=payload.metadata,
    )
    summary = participation_summary(db, user_id=current_user.id if current_user else None, guest_session_id=activity.guest_session_id)
    db.commit()
    return {"ok": True, "activity": _serialize_activity(activity), "participation": summary}


@router.get("/summary")
def get_participation_summary(
    request: Request,
    x_guest_session_id: str | None = Header(default=None, alias="X-Guest-Session-Id"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    guest_session_id = x_guest_session_id or request.cookies.get("simba_guest_session")
    summary = participation_summary(db, user_id=current_user.id if current_user else None, guest_session_id=guest_session_id)
    return {"ok": True, "participation": summary}
