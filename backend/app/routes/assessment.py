import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database import get_db_connection
from app.services.leadership_question_map import ROLE_KEYS
from app.services.leadership_scoring import score_assessment

router = APIRouter(prefix="/assessment", tags=["Leadership Assessment"])


class AssessmentSubmitRequest(BaseModel):
    userId: str | None = Field(default=None, min_length=3)
    responses: list[str | int | float] = Field(min_length=30, max_length=30)


@router.post("/submit")
def submit_assessment(payload: AssessmentSubmitRequest):
    user_id = payload.userId or str(uuid4())
    scored = score_assessment(payload.responses)

    scores_blob = {
        "percentages": scored["percentages"],
        "roles": scored["roles"],
        "insights": scored["insights"],
        "coaching": scored["coaching"],
    }

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO leadership_assessments (user_id, responses, scores, version, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                json.dumps(scored["responses"]),
                json.dumps(scores_blob),
                "v1",
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()

    return {
        "userId": user_id,
        "percentages": scored["percentages"],
        "roles": scored["roles"],
        "insights": scored["insights"],
        "coaching": scored["coaching"],
        "rolesIncluded": ROLE_KEYS,
        "version": "v1",
    }


@router.get("/results/{user_id}")
def get_latest_assessment(user_id: str):
    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT user_id, responses, scores, version, created_at
            FROM leadership_assessments
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No assessment found for this user.")

    scores = json.loads(row[2])
    responses = json.loads(row[1])

    return {
        "userId": row[0],
        "responses": responses,
        "percentages": scores.get("percentages", {}),
        "roles": scores.get("roles", {}),
        "insights": scores.get("insights", {}),
        "coaching": scores.get("coaching", ""),
        "version": row[3] or "v1",
        "createdAt": row[4],
    }


@router.get("/analytics/roles")
def role_analytics():
    with get_db_connection() as conn:
        rows = conn.execute("SELECT scores FROM leadership_assessments").fetchall()

    if not rows:
        return {
            "assessments": 0,
            "role_counts": {role: 0 for role in ROLE_KEYS},
            "average_percentages": {role: 0.0 for role in ROLE_KEYS},
        }

    role_counts = {role: 0 for role in ROLE_KEYS}
    sums = {role: 0.0 for role in ROLE_KEYS}

    for row in rows:
        scores = json.loads(row[0])
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
