from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import chat, portal, voice

import os

# ---------------------------------------------------
# APP INITIALIZATION
# ---------------------------------------------------

app = FastAPI(
    title="Mufasa Knowledge Bank API",
    description=(
        "Backend intelligence for the Prince of Pan-Africa platform — "
        "integrating text, voice, and image AI features aligned with the Maat principles."
    ),
    version="1.0.0",
)

# ---------------------------------------------------
# CORS CONFIGURATION
# ---------------------------------------------------

default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://prince-of-pan-africa.onrender.com",
    "https://mufasa-knowledge-bank.onrender.com",
    "https://simbawaujamaa.com",
    "https://www.simbawaujamaa.com",
]

raw_allowed_origins = os.getenv("ALLOWED_ORIGINS", "")

allowed_origins = (
    [origin.strip() for origin in raw_allowed_origins.split(",") if origin.strip()]
    if raw_allowed_origins
    else default_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# STATIC FILES (FOR MEDIA / PILOT STORAGE)
# ---------------------------------------------------

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ---------------------------------------------------
# ROUTERS
# ---------------------------------------------------

app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(portal.router, prefix="/portal", tags=["Portals"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])

# ---------------------------------------------------
# CORE SYSTEM ROUTES
# ---------------------------------------------------

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
    return {
        "ok": True,
        "service": "Mufasa Knowledge Bank",
        "environment": os.getenv("ENVIRONMENT", "production"),
    }


@app.get("/info")
def info():
    return {
        "app_name": app.title,
        "version": app.version,
        "static_path": "/static",
        "routes": [route.path for route in app.routes],
    }


# ---------------------------------------------------
# STARTUP EVENT
# ---------------------------------------------------

@app.on_event("startup")
async def startup_event():
    print("🔥 Mufasa Knowledge Bank is awake and ready to serve the Pride!")
