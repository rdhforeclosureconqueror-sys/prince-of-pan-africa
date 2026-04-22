import json
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ActivityLog, LeadershipAssessment, User
from app.services.leadership_question_map import ROLE_KEYS
from app.services.leadership_scoring import score_assessment

router = APIRouter(prefix="/assessment", tags=["Leadership Assessment"])
logger = logging.getLogger(__name__)


class AssessmentSubmitRequest(BaseModel):
    userId: str | None = Field(default=None, min_length=1)
    accountId: str | None = Field(default=None, min_length=1)
    parentId: str | None = Field(default=None, min_length=1)
    childId: str | None = Field(default=None, min_length=1)
    submissionId: str | None = Field(default=None, min_length=1)
    responses: list[str | int | float] = Field(min_length=30, max_length=30)


def _resolve_or_create_user(db: Session, user_identifier: str | None) -> User:
    if user_identifier:
        if user_identifier.isdigit():
            user = db.query(User).filter(User.id == int(user_identifier)).first()
            if user:
                return user

        lookup_email = (
            user_identifier
            if "@" in user_identifier
            else f"member+{user_identifier}@local.mufasa"
        )
        user = db.query(User).filter(User.email == lookup_email).first()
        if user:
            return user

        new_user = User(
            email=lookup_email,
            password_hash="",
            role="member",
        )
        db.add(new_user)
        db.flush()
        return new_user

    new_user = User(
        email=f"member-{uuid4()}@local.mufasa",
        password_hash="",
        role="member",
    )
    db.add(new_user)
    db.flush()
    return new_user


def _serialize_assessment(row: LeadershipAssessment) -> dict:
    scores = json.loads(row.scores)
    responses = json.loads(row.responses)
    return {
        "assessmentId": str(row.id),
        "submissionId": row.submission_id,
        "userId": str(row.user_id),
        "accountId": row.account_id,
        "parentId": row.parent_id,
        "childId": row.child_id,
        "responses": responses,
        "percentages": scores.get("percentages", {}),
        "roles": scores.get("roles", {}),
        "insights": scores.get("insights", {}),
        "coaching": scores.get("coaching", ""),
        "version": row.version or "v1",
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "saved": True,
    }


@router.post("/submit")
def submit_assessment(payload: AssessmentSubmitRequest, db: Session = Depends(get_db)):
    user = _resolve_or_create_user(db, payload.userId)

    scored = score_assessment(payload.responses)
    submission_id = payload.submissionId or str(uuid4())

    scores_blob = {
        "percentages": scored["percentages"],
        "roles": scored["roles"],
        "insights": scored["insights"],
        "coaching": scored["coaching"],
    }

    record = LeadershipAssessment(
        user_id=user.id,
        account_id=payload.accountId,
        parent_id=payload.parentId,
        child_id=payload.childId,
        submission_id=submission_id,
        responses=json.dumps(scored["responses"]),
        scores=json.dumps(scores_blob),
        version="v1",
    )
    db.add(record)
    db.add(ActivityLog(user_id=user.id, action="assessment_submitted"))
    db.commit()
    db.refresh(record)

    logger.info(
        "assessment_saved assessment_id=%s submission_id=%s user_id=%s account_id=%s parent_id=%s child_id=%s",
        record.id,
        submission_id,
        user.id,
        payload.accountId,
        payload.parentId,
        payload.childId,
    )

    return {
        "assessmentId": str(record.id),
        "submissionId": submission_id,
        "userId": str(user.id),
        "accountId": payload.accountId,
        "parentId": payload.parentId,
        "childId": payload.childId,
        "percentages": scored["percentages"],
        "roles": scored["roles"],
        "insights": scored["insights"],
        "coaching": scored["coaching"],
        "rolesIncluded": ROLE_KEYS,
        "version": "v1",
        "saved": True,
    }


@router.get("/results/{user_id}")
def get_latest_assessment(user_id: str, db: Session = Depends(get_db)):
    query = db.query(LeadershipAssessment)

    if user_id.isdigit():
        query = query.filter(LeadershipAssessment.user_id == int(user_id))
    else:
        user = _resolve_or_create_user(db, user_id)
        query = query.filter(LeadershipAssessment.user_id == user.id)

    row = query.order_by(LeadershipAssessment.id.desc()).first()

    if not row:
        raise HTTPException(status_code=404, detail="No assessment found for this user.")

    logger.info(
        "assessment_latest_selected assessment_id=%s submission_id=%s user_id=%s",
        row.id,
        row.submission_id,
        row.user_id,
    )

    return _serialize_assessment(row)


@router.get("/dashboard/{user_id}")
def get_assessment_dashboard(user_id: str, db: Session = Depends(get_db)):
    query = db.query(LeadershipAssessment)

    if user_id.isdigit():
        query = query.filter(LeadershipAssessment.user_id == int(user_id))
    else:
        user = _resolve_or_create_user(db, user_id)
        query = query.filter(LeadershipAssessment.user_id == user.id)

    rows = query.order_by(LeadershipAssessment.id.desc()).all()
    if not rows:
        raise HTTPException(status_code=404, detail="No assessment found for this user.")

    latest = _serialize_assessment(rows[0])
    history = [
        {
            "assessmentId": str(row.id),
            "submissionId": row.submission_id,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "roles": json.loads(row.scores).get("roles", {}),
        }
        for row in rows
    ]

    logger.info(
        "assessment_dashboard_selected user_id=%s latest_assessment_id=%s history_count=%s",
        latest["userId"],
        latest["assessmentId"],
        len(history),
    )

    return {
        "saved": True,
        "latest": latest,
        "history": history,
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
