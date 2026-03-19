from fastapi import APIRouter

router = APIRouter(tags=["Member"])


@router.get("/member/overview")
def get_member_overview():
    return {
        "status": "ok",
        "message": "overview working",
    }


@router.get("/member/activity")
def get_member_activity():
    return {
        "status": "ok",
        "message": "activity working",
    }
