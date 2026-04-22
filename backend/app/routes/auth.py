from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MemberProfile, User
from app.security import hash_password

router = APIRouter(prefix="/auth", tags=["Auth"])

SESSION_COOKIE = "mufasa_session"


class AuthPayload(BaseModel):
    email: str
    password: str = Field(min_length=6, max_length=128)




def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _find_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = _normalize_email(email)
    return (
        db.query(User)
        .filter(func.lower(func.trim(User.email)) == normalized_email)
        .order_by(User.id.asc())
        .first()
    )

def _set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=str(user_id),
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 30,
    )


def _serialize_user(user: User) -> dict:
    is_admin = user.role in {"admin", "superadmin"}
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_admin": is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _current_user(request: Request, db: Session) -> User | None:
    raw_user_id = request.cookies.get(SESSION_COOKIE)
    if not raw_user_id:
        return None

    try:
        user_id = int(raw_user_id)
    except ValueError:
        return None

    return db.query(User).filter(User.id == user_id).first()


@router.get("/me")
def auth_me(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)

    if not user:
        return {"ok": True, "auth": False, "authenticated": False, "user": None}

    return {
        "ok": True,
        "auth": True,
        "authenticated": True,
        "user": _serialize_user(user),
    }


@router.post("/join", status_code=status.HTTP_201_CREATED)
def auth_join(payload: AuthPayload, response: Response, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(payload.email)
    if "@" not in normalized_email:
        raise HTTPException(status_code=422, detail="Valid email is required")

    existing = _find_user_by_email(db, normalized_email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(email=normalized_email, password_hash=hash_password(payload.password), role="member")
    db.add(user)
    db.flush()

    db.add(
        MemberProfile(
            user_id=user.id,
            role="member",
            attributes={"status": "active", "onboarding": "joined"},
        )
    )
    db.commit()

    _set_session_cookie(response, user.id)
    return {"ok": True, "joined": True, "user": _serialize_user(user)}


@router.post("/login")
def auth_login(payload: AuthPayload, response: Response, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(payload.email)
    user = _find_user_by_email(db, normalized_email)
    if not user or user.password_hash != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    _set_session_cookie(response, user.id)
    return {"ok": True, "authenticated": True, "user": _serialize_user(user)}


@router.post("/logout")
def auth_logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True, "logged_out": True}
