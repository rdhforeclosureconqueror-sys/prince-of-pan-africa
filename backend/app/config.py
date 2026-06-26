import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    # SKILL_WORLD_TTS_URL is the canonical public aiVoice /speak endpoint for TTS.
    # Legacy AIVOICE_BASE_URL / OPENVOICE_URL are kept for older non-Skill-World callers,
    # but they must not override the canonical Skill World URL.
    SKILL_WORLD_TTS_URL: str = os.getenv(
        "SKILL_WORLD_TTS_URL",
        "https://aivoice-wmrv.onrender.com/speak",
    )
    SKILL_WORLD_TTS_TOKEN: str = os.getenv("SKILL_WORLD_TTS_TOKEN", "")
    AIVOICE_BASE_URL: str = (
        os.getenv("AIVOICE_BASE_URL")
        or os.getenv("OPENVOICE_URL")
        or "https://aivoice-wmrv.onrender.com"
    )
    AIVOICE_API_KEY: str = os.getenv("AIVOICE_API_KEY", "")
    BASE_URL: str = os.getenv("BASE_URL", "https://mufasa-knowledge-bank.onrender.com")
    AUDIO_STORAGE_DIR: str = os.getenv("AUDIO_STORAGE_DIR", "")
    BOOK_COVER_STORAGE_DIR: str = os.getenv("BOOK_COVER_STORAGE_DIR", "/var/data/static/book-covers")
    ENABLE_TEXT_BOOK_ORGANIZER: bool = os.getenv("ENABLE_TEXT_BOOK_ORGANIZER", "false").strip().lower() in {"1", "true", "yes", "on"}
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_COMMUNITY_PRICE_ID: str = os.getenv("STRIPE_COMMUNITY_PRICE_ID", "")
    STRIPE_BUILDER_PRICE_ID: str = os.getenv("STRIPE_BUILDER_PRICE_ID", "")
    ENABLE_STRIPE_CHECKOUT: bool = os.getenv("ENABLE_STRIPE_CHECKOUT", "false").strip().lower() in {"1", "true", "yes", "on"}
    GARVEY_BASE_URL: str = os.getenv("GARVEY_BASE_URL", "")
    GARVEY_TRANSFER_SECRET: str = os.getenv("GARVEY_TRANSFER_SECRET", "")
    GARVEY_ALLOWED_ISSUER: str = os.getenv("GARVEY_ALLOWED_ISSUER", "simba_wajuma")
    GARVEY_CALLBACK_SECRET: str = os.getenv("GARVEY_CALLBACK_SECRET", "")

    ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION: bool = os.getenv("ENABLE_MUTUAL_AID_RUNTIME_FOUNDATION", "true").strip().lower() in {"1", "true", "yes", "on"}
    MUTUAL_AID_REQUESTS_ENABLED: bool = os.getenv("MUTUAL_AID_REQUESTS_ENABLED", os.getenv("ENABLE_MUTUAL_AID_REQUEST_INTAKE", "false")).strip().lower() in {"1", "true", "yes", "on"}
    ENABLE_MUTUAL_AID_REQUEST_INTAKE: bool = MUTUAL_AID_REQUESTS_ENABLED
    MUTUAL_AID_REVIEW_ENABLED: bool = os.getenv("MUTUAL_AID_REVIEW_ENABLED", os.getenv("ENABLE_MUTUAL_AID_REVIEW_WORKFLOW", "false")).strip().lower() in {"1", "true", "yes", "on"}
    ENABLE_MUTUAL_AID_REVIEW_WORKFLOW: bool = MUTUAL_AID_REVIEW_ENABLED
    MUTUAL_AID_DECISIONS_ENABLED: bool = os.getenv("MUTUAL_AID_DECISIONS_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    ENABLE_MUTUAL_AID_PAYMENTS: bool = os.getenv("ENABLE_MUTUAL_AID_PAYMENTS", "false").strip().lower() in {"1", "true", "yes", "on"}
    MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED: bool = os.getenv("MUTUAL_AID_FINANCIAL_CONTROLS_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED: bool = os.getenv("MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


settings = Settings()
