from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me")
def auth_me():
    return {
        "ok": True,
        "auth": True,
        "authenticated": True,
        "user": {
            "email": "rdhforeclosureconqueror@gmail.com",
            "role": "admin",
        },
    }
