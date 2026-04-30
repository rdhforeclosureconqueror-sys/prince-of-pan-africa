from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.authz import user_has_permission
from app.database import get_db
from app.models import User
from app.session import SESSION_COOKIE, parse_session_cookie_value


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    raw_session = request.cookies.get(SESSION_COOKIE)
    try:
        session = parse_session_cookie_value(raw_session)
    except Exception:
        return None

    return db.query(User).filter(User.id == session["user_id"]).first()


def require_auth(current_user: User | None = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


def require_permission(permission_name: str):
    def _require_permission(
        current_user: User = Depends(require_auth),
        db: Session = Depends(get_db),
    ) -> User:
        if user_has_permission(db, current_user, permission_name):
            return current_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return _require_permission




def is_local_or_dev_environment() -> bool:
    from app.session import should_use_secure_cookie

    return not should_use_secure_cookie()
