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
    ENABLE_TEXT_BOOK_ORGANIZER: bool = os.getenv("ENABLE_TEXT_BOOK_ORGANIZER", "false").strip().lower() in {"1", "true", "yes", "on"}


settings = Settings()
