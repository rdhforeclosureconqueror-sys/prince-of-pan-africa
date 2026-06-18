import os
import logging
import subprocess
import asyncio

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import (
    SessionLocal,
    enforce_database_url_for_production,
    get_database_type,
    init_db,
    is_production_like_environment,
    is_unsafe_sqlite_fallback,
)
from app.routes import admin, assessment, audio, audiobook, auth, billing, chat, discord, member, participation, portal, skill_world, system, tts, voice
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

CUSTOM_API_DOMAIN = "api.simbawaujamaa.com"
PUBLIC_API_BASE_ENV_KEYS = ("VITE_API_BASE_URL", "PUBLIC_API_BASE_URL", "BACKEND_URL")


def _configured_public_api_bases() -> dict[str, str]:
    return {
        key: value.strip()
        for key in PUBLIC_API_BASE_ENV_KEYS
        if (value := os.getenv(key, "").strip())
    }


def _log_custom_api_domain_status() -> None:
    configured_bases = _configured_public_api_bases()
    custom_domain_bases = {
        key: value
        for key, value in configured_bases.items()
        if CUSTOM_API_DOMAIN in value
    }
    if custom_domain_bases:
        logger.info(
            "%s is configured in public API base environment values %s. "
            "Use this same-site API domain only after Render verifies DNS and certificate "
            "for prince-of-pan-africa-backend; once verified, it is valid for production.",
            CUSTOM_API_DOMAIN,
            custom_domain_bases,
        )

default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://prince-of-pan-africa.onrender.com",
    "https://prince-of-pan-africa-frontend.onrender.com",
    "https://mufasa-knowledge-bank.onrender.com",
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

    tracked_paths = {
        "/admin/ai/overview",
        "/admin/overview",
        "/admin/activity-stream",
        "/auth/me",
        "/member/overview",
        "/member/activity",
    }
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
BOOK_COVER_STORAGE_DIR = os.getenv("BOOK_COVER_STORAGE_DIR", "/var/data/static/book-covers")
os.makedirs(BOOK_COVER_STORAGE_DIR, exist_ok=True)
app.mount("/static/audio", StaticFiles(directory=str(chat.STATIC_AUDIO_DIR)), name="static-audio")
app.mount("/static/book-covers", StaticFiles(directory=BOOK_COVER_STORAGE_DIR), name="static-book-covers")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

GENERATED_SKILL_WORLD_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "generated-audio", "skill-world")
os.makedirs(GENERATED_SKILL_WORLD_AUDIO_DIR, exist_ok=True)
app.mount(
    "/generated-audio/skill-world",
    StaticFiles(directory=GENERATED_SKILL_WORLD_AUDIO_DIR),
    name="generated-skill-world-audio",
)

app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(portal.router, prefix="/portal", tags=["Portals"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(skill_world.router, tags=["Skill World Audio"])
app.include_router(system.router)
app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(tts.router)
app.include_router(assessment.router)
app.include_router(admin.router)
app.include_router(admin.legacy_router)
app.include_router(member.router)
app.include_router(participation.router)
app.include_router(audiobook.router)
app.include_router(audio.router)
app.include_router(discord.router)


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
    details = {"database": "unknown", "session": "unknown", "database_mode": get_database_type()}
    try:
        from verification.verification_engine import check_database

        db_check = check_database()
        db_ok = bool(db_check.get("connected"))
        details["database"] = "ok" if db_ok else "failed"
        details["database_mode"] = db_check.get("persistence_mode", details["database_mode"])
        details["database_unsafe_fallback"] = bool(db_check.get("unsafe_fallback", False))
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

    if is_production_like_environment() and is_unsafe_sqlite_fallback():
        details["database"] = "failed"
        details["database_mode"] = "sqlite_fallback_unsafe"
        status_label = "failed"

    return {
        "status": status_label,
        "service": "Mufasa Knowledge Bank",
        "details": details,
    }


@app.get("/info")
def info():
    commit_sha = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("GIT_COMMIT")
        or os.getenv("SOURCE_COMMIT")
        or ""
    ).strip()
    if not commit_sha:
        try:
            commit_sha = (
                subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
            )
        except Exception:
            commit_sha = "unknown"

    environment = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "unknown").strip() or "unknown"
    return {
        "app_name": app.title,
        "version": app.version,
        "build_commit": commit_sha,
        "environment": environment,
        "database_type": get_database_type(),
        "static_path": "/static",
        "routes": [route.path for route in app.routes],
    }


@app.on_event("startup")
async def startup_event():
    _log_custom_api_domain_status()
    enforce_database_url_for_production()
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


@app.on_event("startup")
async def start_discord_daily_fact_loop():
    from app.services.discord_bridge import discord_bridge, run_daily_black_economics_loop

    if discord_bridge.configured and discord_bridge.channel_id("black_economics"):
        asyncio.create_task(run_daily_black_economics_loop())

