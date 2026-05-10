from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.authz import user_has_permission
from app.database import get_db
from app.models import User
from app.session import SESSION_COOKIE, parse_session_cookie_value

logger = logging.getLogger("mufasa-auth")


def _session_user_id(request: Request) -> tuple[bool, int | None]:
    raw_session = request.cookies.get(SESSION_COOKIE)
    if not raw_session:
        return False, None

    try:
        session = parse_session_cookie_value(raw_session)
    except Exception:
        return True, None

    return True, session["user_id"]


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    cookie_present, user_id = _session_user_id(request)
    if not cookie_present or user_id is None:
        return None

    return db.query(User).filter(User.id == user_id).first()


def _log_member_auth_failure(
    request: Request,
    status_code: int,
    permission_name: str,
    cookie_present: bool,
    session_user_id: int | None,
    resolved_user: User | None,
    permission_missing: bool,
) -> None:
    if not request.url.path.startswith("/member/"):
        return

    logger.info(
        "member auth failure path=%s status=%s cookie_present=%s session_user_id=%s user_resolved=%s "
        "resolved_user_id=%s required_permission=%s permission_missing=%s origin=%s",
        request.url.path,
        status_code,
        cookie_present,
        session_user_id,
        bool(resolved_user),
        resolved_user.id if resolved_user else None,
        permission_name,
        permission_missing,
        request.headers.get("origin"),
    )


def require_auth(current_user: User | None = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


def require_permission(permission_name: str):
    def _require_permission(
        request: Request,
        db: Session = Depends(get_db),
    ) -> User:
        cookie_present, session_user_id = _session_user_id(request)
        current_user = None
        if session_user_id is not None:
            current_user = db.query(User).filter(User.id == session_user_id).first()

        if not current_user:
            _log_member_auth_failure(
                request=request,
                status_code=status.HTTP_401_UNAUTHORIZED,
                permission_name=permission_name,
                cookie_present=cookie_present,
                session_user_id=session_user_id,
                resolved_user=current_user,
                permission_missing=False,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

        if user_has_permission(db, current_user, permission_name):
            return current_user

        _log_member_auth_failure(
            request=request,
            status_code=status.HTTP_403_FORBIDDEN,
            permission_name=permission_name,
            cookie_present=cookie_present,
            session_user_id=session_user_id,
            resolved_user=current_user,
            permission_missing=True,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return _require_permission



def is_local_or_dev_environment() -> bool:
    from app.session import should_use_secure_cookie

    return not should_use_secure_cookie()
