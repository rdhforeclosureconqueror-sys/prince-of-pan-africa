from fastapi import APIRouter

router = APIRouter(prefix="/admin/ai", tags=["Admin AI"])


@router.get("/overview")
def admin_ai_overview():
    return {
        "ok": True,
        "data": {
            "totals": {"motions": 0, "voices": 0, "journals": 0, "avg_score": 0},
            "byType": [],
            "models": [],
        },
    }


@router.get("/members")
def admin_ai_members():
    return {"ok": True, "members": []}


@router.get("/profiles")
def admin_ai_profiles():
    return {"ok": True, "profiles": []}


# Backward-compatible admin surfaces used by legacy and pilot dashboards.
legacy_router = APIRouter(prefix="/admin", tags=["Admin Compatibility"])


@legacy_router.get("/overview")
def admin_overview_compat():
    return {
        "ok": True,
        "member_count": 0,
        "total_shares": 0,
        "total_stars": 0,
        "total_bd": 0,
        "data": {
            "totals": {"motions": 0, "voices": 0, "journals": 0, "avg_score": 0},
            "byType": [],
            "models": [],
        },
    }


@legacy_router.get("/members")
def admin_members_compat():
    return {"ok": True, "members": []}


@legacy_router.get("/profiles")
def admin_profiles_compat():
    return {"ok": True, "profiles": []}


@legacy_router.get("/shares")
def admin_shares_compat():
    return {"ok": True, "shares": []}


@legacy_router.get("/reviews")
def admin_reviews_compat():
    return {"ok": True, "reviews": []}


@legacy_router.get("/activity-stream")
def admin_activity_stream_compat():
    return {"ok": True, "items": []}


@legacy_router.get("/holistic/overview")
def admin_holistic_overview_compat():
    return {"ok": True, "holistic": []}
