from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import auth, chat, portal, voice
import os

app = FastAPI(
    title="Prince of Pan-Africa Backend",
    description="Core backend for the Prince of Pan-Africa platform",
    version="1.0.0",
)

raw_allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [origin.strip() for origin in raw_allowed_origins.split(",") if origin.strip()]
if not allowed_origins:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(portal.router, prefix="/portal", tags=["Portals"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Prince of Pan-Africa Backend",
        "message": "Prince of Pan-Africa Backend is live. Visit /docs for API routes.",
    }


@app.get("/health")
def health():
    return {"ok": True, "service": "Prince of Pan-Africa Backend", "environment": "production"}


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
    print("🔥 Prince of Pan-Africa Backend is awake and ready.")
