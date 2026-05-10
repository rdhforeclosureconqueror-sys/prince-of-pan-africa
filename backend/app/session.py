from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

SESSION_COOKIE = "mufasa_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30


class SessionValidationError(ValueError):
    pass


def _session_secret() -> str:
    return os.getenv("SESSION_SECRET", "")


def get_session_secret() -> str:
    secret = _session_secret().strip()
    if secret:
        return secret

    insecure_ok = os.getenv("ALLOW_INSECURE_DEV_SESSION_SECRET", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if insecure_ok and not should_use_secure_cookie():
        return "dev-insecure-session-secret"

    raise SessionValidationError(
        "SESSION_SECRET is required. Set SESSION_SECRET in production; for local/dev/test only, "
        "you may set ALLOW_INSECURE_DEV_SESSION_SECRET=true to use an explicit fallback."
    )


def _urlsafe_b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _urlsafe_b64decode(data: str) -> bytes:
    pad = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode((data + pad).encode("ascii"))


def _sign(payload_bytes: bytes, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return _urlsafe_b64encode(signature)


def build_session_cookie_value(user_id: int, issued_at: int | None = None) -> str:
    secret = get_session_secret()

    payload: dict[str, Any] = {
        "user_id": int(user_id),
        "issued_at": int(issued_at or time.time()),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _urlsafe_b64encode(payload_bytes)
    signature_b64 = _sign(payload_bytes, secret)
    return f"{payload_b64}.{signature_b64}"


def parse_session_cookie_value(cookie_value: str | None) -> dict[str, int]:
    if not cookie_value:
        raise SessionValidationError("Missing session cookie")

    secret = get_session_secret()

    try:
        payload_b64, signature_b64 = cookie_value.split(".", 1)
        payload_bytes = _urlsafe_b64decode(payload_b64)
    except Exception as exc:  # pragma: no cover
        raise SessionValidationError("Malformed session cookie") from exc

    expected_signature = _sign(payload_bytes, secret)
    if not hmac.compare_digest(signature_b64, expected_signature):
        raise SessionValidationError("Invalid session signature")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise SessionValidationError("Malformed session payload") from exc

    user_id = payload.get("user_id")
    issued_at = payload.get("issued_at")
    if not isinstance(user_id, int) or not isinstance(issued_at, int):
        raise SessionValidationError("Invalid session payload fields")

    if issued_at <= 0 or time.time() - issued_at > SESSION_MAX_AGE_SECONDS:
        raise SessionValidationError("Session expired")

    return {"user_id": user_id, "issued_at": issued_at}


def is_production_like_cookie_environment() -> bool:
    env = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "").strip().lower()
    return env not in {"", "local", "dev", "development", "test", "testing"}


def should_use_secure_cookie() -> bool:
    return is_production_like_cookie_environment()


def get_session_cookie_domain() -> str | None:
    domain = os.getenv("SESSION_COOKIE_DOMAIN", "").strip()
    return domain or None


def get_session_cookie_samesite() -> str:
    configured = os.getenv("SESSION_COOKIE_SAMESITE", "").strip().lower()
    if configured in {"lax", "strict", "none"}:
        return configured

    # Production is intended to run the browser-facing API on api.simbawaujamaa.com,
    # which is same-site with simbawaujamaa.com and works with Lax cookies. If a
    # temporary cross-site API URL is unavoidable, set SESSION_COOKIE_SAMESITE=None.
    return "lax"
