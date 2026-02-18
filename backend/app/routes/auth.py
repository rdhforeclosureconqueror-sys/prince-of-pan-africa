from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import os
import hmac
import hashlib
import base64
import json
import time

router = APIRouter()
JWT_SECRET = os.getenv("JWT_SECRET", "prototype-secret")
JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", "86400"))

USERS = {}


class RegisterPayload(BaseModel):
    email: str
    password: str
    display_name: str | None = None


class LoginPayload(BaseModel):
    email: str
    password: str


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(data: str) -> str:
    sig = hmac.new(JWT_SECRET.encode(), data.encode(), hashlib.sha256).digest()
    return _b64url(sig)


def make_token(user: dict) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(
        json.dumps(
            {
                "sub": user["id"],
                "email": user["email"],
                "role": user.get("role", "member"),
                "exp": int(time.time()) + JWT_EXP_SECONDS,
            }
        ).encode()
    )
    body = f"{header}.{payload}"
    return f"{body}.{_sign(body)}"


def parse_token(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token")
        body = f"{parts[0]}.{parts[1]}"
        if not hmac.compare_digest(parts[2], _sign(body)):
            raise ValueError("Invalid signature")

        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        if payload.get("exp", 0) < int(time.time()):
            raise ValueError("Token expired")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
def register(payload: RegisterPayload):
    email = payload.email.lower().strip()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    if email in USERS:
        raise HTTPException(status_code=400, detail="User already exists")

    user = {
        "id": f"user-{len(USERS)+1}",
        "email": email,
        "display_name": payload.display_name or email.split("@")[0],
        "role": "admin" if len(USERS) == 0 else "member",
        "password_hash": _hash_password(payload.password),
    }
    USERS[email] = user
    return {"ok": True, "user": {k: v for k, v in user.items() if k != "password_hash"}}


@router.post("/login")
def login(payload: LoginPayload):
    email = payload.email.lower().strip()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    user = USERS.get(email)
    if not user or user["password_hash"] != _hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    public_user = {k: v for k, v in user.items() if k != "password_hash"}
    token = make_token(public_user)
    return {"ok": True, "token": token, "user": public_user}


@router.get("/me")
def me(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = parse_token(authorization.split(" ", 1)[1])
    user = USERS.get(payload["email"].lower())
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    public_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {"ok": True, "auth": True, "user": public_user}
