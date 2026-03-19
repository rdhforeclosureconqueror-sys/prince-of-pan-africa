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
