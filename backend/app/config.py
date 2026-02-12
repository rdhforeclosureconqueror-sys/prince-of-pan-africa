import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AIVOICE_BASE_URL: str = os.getenv("AIVOICE_BASE_URL", "https://aivoice-wmrv.onrender.com")
    AIVOICE_API_KEY: str = os.getenv("AIVOICE_API_KEY", "")
    BASE_URL: str = os.getenv("BASE_URL", "https://mufasa-knowledge-bank.onrender.com")


settings = Settings()
