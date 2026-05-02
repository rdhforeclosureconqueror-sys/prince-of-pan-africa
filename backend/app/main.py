import os
import logging

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import SessionLocal, init_db
from app.routes import admin, assessment, audiobook, auth, chat, member, portal, system, tts, voice
from app.services.admin_seed import seed_admin
from app.authz import seed_rbac_defaults
from app.session import SessionValidationError, get_session_secret

app = FastAPI(
    title="Mufasa Knowledge Bank API",
    description=(
        "Backend intelligence for the Prince of Pan-Africa platform — "
        "integrating text, voice, and image AI features aligned with the Maat principles."
    ),
    version="1.0.0",
)

logger = logging.getLogger("mufasa-cors")

default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://prince-of-pan-africa.onrender.com",
    "https://prince-of-pan-africa-frontend.onrender.com",
    "https://mufasa-knowledge-bank.onrender.com",
    "https://api.simbawaujamaa.com",
    "https://simbawaujamaa.com",
    "https://www.simbawaujamaa.com",
    "https://simbawajamaa.com",
    "https://www.simbawajamaa.com",
]


def _parse_origins(raw: str) -> list[str]:
    parsed = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    deduped: list[str] = []
    for origin in parsed:
        if origin not in deduped:
            deduped.append(origin)
    return deduped


raw_allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
raw_cors_allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
origins_source = "default_origins"
raw_origins = ""

if raw_allowed_origins.strip():
    raw_origins = raw_allowed_origins
    origins_source = "ALLOWED_ORIGINS"
elif raw_cors_allowed_origins.strip():
    raw_origins = raw_cors_allowed_origins
    origins_source = "CORS_ALLOWED_ORIGINS"

allowed_origins = _parse_origins(raw_origins) if raw_origins else default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_tts_preflight(request: Request, call_next):
    if request.method == "OPTIONS" and request.url.path == "/chat/tts":
        logger.info(
            "OPTIONS /chat/tts preflight origin=%s acr_method=%s acr_headers=%s",
            request.headers.get("origin"),
            request.headers.get("access-control-request-method"),
            request.headers.get("access-control-request-headers"),
        )

    response = await call_next(request)

    if request.method == "OPTIONS" and request.url.path == "/chat/tts":
        logger.info(
            "OPTIONS /chat/tts response status=%s allow_origin=%s",
            response.status_code,
            response.headers.get("access-control-allow-origin"),
        )

    return response


@app.middleware("http")
async def log_admin_request_context(request: Request, call_next):
    response = await call_next(request)

    tracked_paths = {"/admin/ai/overview", "/admin/overview", "/admin/activity-stream", "/auth/me"}
    if request.url.path in tracked_paths:
        user_id = None
        cookie_present = False
        try:
            from app.session import SESSION_COOKIE, parse_session_cookie_value

            raw_session = request.cookies.get(SESSION_COOKIE)
            cookie_present = bool(raw_session)
            if raw_session:
                parsed = parse_session_cookie_value(raw_session)
                user_id = parsed.get("user_id")
        except Exception:
            user_id = None

        logger.info(
            "REQ method=%s path=%s status=%s user_id=%s cookie_present=%s origin=%s",
            request.method,
            request.url.path,
            response.status_code,
            user_id,
            cookie_present,
            request.headers.get("origin"),
        )

    return response

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(portal.router, prefix="/portal", tags=["Portals"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(system.router)
app.include_router(auth.router)
app.include_router(tts.router)
app.include_router(assessment.router)
app.include_router(admin.router)
app.include_router(admin.legacy_router)
app.include_router(member.router)
app.include_router(audiobook.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Mufasa Knowledge Bank",
        "frontend": "Prince of Pan-Africa",
        "message": "Mufasa Knowledge Bank is live. Visit /docs for API routes.",
    }


@app.get("/health")
def health():
    status_label = "ok"
    details = {"database": "unknown", "session": "unknown"}
    try:
        from verification.verification_engine import check_database

        db_ok = bool(check_database().get("connected"))
        details["database"] = "ok" if db_ok else "failed"
        if not db_ok:
            status_label = "degraded"
    except Exception:
        details["database"] = "failed"
        status_label = "degraded"

    try:
        get_session_secret()
        details["session"] = "ok"
    except SessionValidationError:
        details["session"] = "failed"
        status_label = "failed"

    return {
        "status": status_label,
        "service": "Mufasa Knowledge Bank",
        "details": details,
    }


@app.get("/info")
def info():
    return {
        "app_name": app.title,
        "version": app.version,
        "static_path": "/static",
        "routes": [route.path for route in app.routes],
    }


@app.on_event("startup")
async def startup_event():
    get_session_secret()
    init_db()
    result = seed_admin()
    db = SessionLocal()
    try:
        seed_rbac_defaults(db)
    finally:
        db.close()
    logger.info(
        "CORS config source=%s ALLOWED_ORIGINS_raw=%s CORS_ALLOWED_ORIGINS_raw=%s parsed_allowed_origins=%s",
        origins_source,
        raw_allowed_origins,
        raw_cors_allowed_origins,
        allowed_origins,
    )
    print(f"Admin seed status: {result}")
    print("🔥 Mufasa Knowledge Bank is awake and ready to serve the Pride!")
