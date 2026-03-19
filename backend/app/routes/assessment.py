import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ActivityLog, LeadershipAssessment, User
from app.services.leadership_question_map import ROLE_KEYS
from app.services.leadership_scoring import score_assessment

router = APIRouter(prefix="/assessment", tags=["Leadership Assessment"])


class AssessmentSubmitRequest(BaseModel):
    userId: str | None = Field(default=None, min_length=1)
    responses: list[str | int | float] = Field(min_length=30, max_length=30)


def _resolve_or_create_user(db: Session, user_identifier: str | None) -> User:
    if user_identifier:
        if user_identifier.isdigit():
            user = db.query(User).filter(User.id == int(user_identifier)).first()
            if user:
                return user
        user = db.query(User).filter(User.email == user_identifier).first()
        if user:
            return user

    new_user = User(
        email=f"member-{uuid4()}@local.mufasa",
        password_hash="",
        role="member",
    )
    db.add(new_user)
    db.flush()
    return new_user


@router.post("/submit")
def submit_assessment(payload: AssessmentSubmitRequest, db: Session = Depends(get_db)):
    user = _resolve_or_create_user(db, payload.userId)
    scored = score_assessment(payload.responses)

    scores_blob = {
        "percentages": scored["percentages"],
        "roles": scored["roles"],
        "insights": scored["insights"],
        "coaching": scored["coaching"],
    }

    record = LeadershipAssessment(
        user_id=user.id,
        responses=json.dumps(scored["responses"]),
        scores=json.dumps(scores_blob),
        version="v1",
    )
    db.add(record)
    db.add(ActivityLog(user_id=user.id, action="assessment_submitted"))
    db.commit()

    return {
        "userId": str(user.id),
        "percentages": scored["percentages"],
        "roles": scored["roles"],
        "insights": scored["insights"],
        "coaching": scored["coaching"],
        "rolesIncluded": ROLE_KEYS,
        "version": "v1",
    }


@router.get("/results/{user_id}")
def get_latest_assessment(user_id: str, db: Session = Depends(get_db)):
    query = db.query(LeadershipAssessment)
    if user_id.isdigit():
        query = query.filter(LeadershipAssessment.user_id == int(user_id))
    else:
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="No assessment found for this user.")
        query = query.filter(LeadershipAssessment.user_id == user.id)

    row = query.order_by(LeadershipAssessment.id.desc()).first()

    if not row:
        raise HTTPException(status_code=404, detail="No assessment found for this user.")

    scores = json.loads(row.scores)
    responses = json.loads(row.responses)

    return {
        "userId": str(row.user_id),
        "responses": responses,
        "percentages": scores.get("percentages", {}),
        "roles": scores.get("roles", {}),
        "insights": scores.get("insights", {}),
        "coaching": scores.get("coaching", ""),
        "version": row.version or "v1",
        "createdAt": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/analytics/roles")
def role_analytics(db: Session = Depends(get_db)):
    rows = db.query(LeadershipAssessment.scores).all()

    if not rows:
        return {
            "assessments": 0,
            "role_counts": {role: 0 for role in ROLE_KEYS},
            "average_percentages": {role: 0.0 for role in ROLE_KEYS},
        }

    role_counts = {role: 0 for role in ROLE_KEYS}
    sums = {role: 0.0 for role in ROLE_KEYS}

    for (scores_raw,) in rows:
        scores = json.loads(scores_raw)
        roles = scores.get("roles", {})
        percentages = scores.get("percentages", {})

        primary_role = roles.get("primary", "").lower()
        for role in ROLE_KEYS:
            if primary_role == role.lower():
                role_counts[role] += 1
            sums[role] += float(percentages.get(role, 0.0))

    total = len(rows)
    averages = {role: round(sums[role] / total, 2) for role in ROLE_KEYS}

    return {
        "assessments": total,
        "role_counts": role_counts,
        "average_percentages": averages,
    }
