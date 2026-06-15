import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.authz import get_user_permissions, get_user_role_names
from app.dependencies.auth import is_local_or_dev_environment
from app.models import MemberProfile, User
from app.security import hash_password, verify_password
from app.session import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    build_session_cookie_value,
    get_session_cookie_domain,
    get_session_cookie_samesite,
    parse_session_cookie_value,
    should_use_secure_cookie,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("mufasa-auth")


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
    secure_cookie = should_use_secure_cookie()
    cookie_domain = get_session_cookie_domain()
    same_site = get_session_cookie_samesite()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=build_session_cookie_value(user_id),
        httponly=True,
        samesite=same_site,
        secure=secure_cookie,
        max_age=SESSION_MAX_AGE_SECONDS,
        path="/",
        domain=cookie_domain,
    )
    logger.info(
        "session_cookie_set user_id=%s secure=%s samesite=%s domain=%s",
        user_id,
        secure_cookie,
        same_site,
        cookie_domain or "host-only",
    )


def _computed_is_admin(role_names: list[str], permissions: list[str]) -> bool:
    normalized_roles = {str(role).strip().lower() for role in role_names}
    normalized_permissions = {str(permission).strip().lower() for permission in permissions}
    return bool(
        {"admin", "superadmin"}.intersection(normalized_roles)
        or "admin:read_dashboard" in normalized_permissions
    )


def _can_access_organizer(role_names: list[str], permissions: list[str]) -> bool:
    return _computed_is_admin(role_names, permissions) or "book_organizer:create_self" in permissions


def _serialize_user(user: User, role_names: list[str] | None = None, permissions: list[str] | None = None) -> dict:
    role_names = role_names or []
    permissions = permissions or []
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_admin": _computed_is_admin(role_names, permissions),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _current_user(request: Request, db: Session) -> User | None:
    raw_session = request.cookies.get(SESSION_COOKIE)
    try:
        session = parse_session_cookie_value(raw_session)
    except Exception:
        return None

    return db.query(User).filter(User.id == session["user_id"]).first()


def _authorization_payload(db: Session, user: User) -> tuple[dict, MemberProfile | None, list[str], list[str], bool, bool]:
    profile = db.query(MemberProfile).filter(MemberProfile.user_id == user.id).first()
    role_names = get_user_role_names(db, user)
    permissions = sorted(get_user_permissions(db, user))
    is_admin = _computed_is_admin(role_names, permissions)
    can_access_organizer = _can_access_organizer(role_names, permissions)
    payload_user = _serialize_user(user, role_names, permissions)
    return payload_user, profile, role_names, permissions, is_admin, can_access_organizer


@router.get("/me")
def auth_me(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)

    if not user:
        return {
            "ok": True,
            "auth": False,
            "authenticated": False,
            "user": None,
            "rbac": {"roles": [], "permissions": []},
        }

    payload_user, profile, role_names, permissions, is_admin, can_access_organizer = _authorization_payload(db, user)

    logger.info(
        "auth_me_resolved user_id=%s email=%s roles=%s permission_count=%s is_admin=%s can_access_organizer=%s",
        user.id,
        user.email,
        role_names,
        len(permissions),
        is_admin,
        can_access_organizer,
    )

    return {
        "ok": True,
        "auth": True,
        "authenticated": True,
        "user": payload_user,
        "company": (profile.attributes or {}).get("company") if profile else None,
        "member_profile_role": profile.role if profile else None,
        "rbac": {
            "roles": role_names,
            "permissions": permissions,
        },
    }


@router.get("/debug/me")
def auth_debug_me(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload_user, profile, role_names, permissions, is_admin, can_access_organizer = _authorization_payload(db, user)
    if not is_local_or_dev_environment() and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return {
        "ok": True,
        "user_id": user.id,
        "email": user.email,
        "users_role": user.role,
        "member_profile_role": profile.role if profile else None,
        "rbac_roles": role_names,
        "rbac_permissions": permissions,
        "computed_is_admin": is_admin,
        "computed_can_access_organizer": can_access_organizer,
        "user": payload_user,
    }


@router.post("/join", status_code=status.HTTP_201_CREATED)
def auth_join(payload: AuthPayload, response: Response, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(payload.email)
    if "@" not in normalized_email:
        raise HTTPException(status_code=422, detail="Valid email is required")

    existing = _find_user_by_email(db, normalized_email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(email=normalized_email, password_hash=hash_password(payload.password), role="community_member")
    db.add(user)
    db.flush()

    db.add(
        MemberProfile(
            user_id=user.id,
            role="community_member",
            attributes={
                "membership_status": "free",
                "membership_type": "free_member",
                "orientation_status": "not_started",
                "discord_status": "not_connected",
                "onboarding": "joined",
            },
        )
    )
    db.commit()

    payload_user, profile, role_names, permissions, _, _ = _authorization_payload(db, user)
    _set_session_cookie(response, user.id)
    return {
        "ok": True,
        "joined": True,
        "user": payload_user,
        "company": (profile.attributes or {}).get("company") if profile else None,
        "member_profile_role": profile.role if profile else None,
        "rbac": {"roles": role_names, "permissions": permissions},
    }


@router.post("/login")
def auth_login(payload: AuthPayload, response: Response, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(payload.email)
    user = _find_user_by_email(db, normalized_email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    is_valid, should_upgrade_hash = verify_password(payload.password, user.password_hash)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if should_upgrade_hash:
        user.password_hash = hash_password(payload.password)
        db.add(user)
        db.commit()

    payload_user, profile, role_names, permissions, _, _ = _authorization_payload(db, user)
    _set_session_cookie(response, user.id)
    return {
        "ok": True,
        "authenticated": True,
        "user": payload_user,
        "company": (profile.attributes or {}).get("company") if profile else None,
        "member_profile_role": profile.role if profile else None,
        "rbac": {"roles": role_names, "permissions": permissions},
    }


@router.post("/logout")
def auth_logout(response: Response):
    secure_cookie = should_use_secure_cookie()
    same_site = get_session_cookie_samesite()
    response.delete_cookie(
        SESSION_COOKIE,
        samesite=same_site,
        secure=secure_cookie,
        path="/",
        domain=get_session_cookie_domain(),
    )
    return {"ok": True, "logged_out": True}
