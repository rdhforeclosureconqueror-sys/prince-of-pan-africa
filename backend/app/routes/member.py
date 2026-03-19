from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import ActivityLog, LeadershipAssessment, MemberProfile, User

router = APIRouter(tags=["Member"])


@router.get("/member/overview")
def get_member_overview(db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.profile)).order_by(User.id.asc()).first()
    if not user:
        raise HTTPException(status_code=404, detail="No member found")

    profile = user.profile
    assessment_count = db.query(LeadershipAssessment).filter(LeadershipAssessment.user_id == user.id).count()
    activity_count = db.query(ActivityLog).filter(ActivityLog.user_id == user.id).count()

    return {
        "status": "ok",
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "member_profile": {
            "id": profile.id if profile else None,
            "role": (profile.role if profile else user.role),
            "attributes": profile.attributes if profile else {},
        },
        "summary_stats": {
            "assessment_count": assessment_count,
            "activity_count": activity_count,
        },
    }


@router.get("/member/activity")
def get_member_activity(limit: int = 10, db: Session = Depends(get_db)):
    user = db.query(User).order_by(User.id.asc()).first()
    if not user:
        raise HTTPException(status_code=404, detail="No member found")

    entries = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.timestamp.desc())
        .limit(max(1, min(limit, 50)))
        .all()
    )

    return {
        "status": "ok",
        "user_id": user.id,
        "activity": [
            {
                "id": entry.id,
                "action": entry.action,
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            }
            for entry in entries
        ],
    }
