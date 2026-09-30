import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PERSONAS_DIR = BASE_DIR / "personas"
UI_DIR = BASE_DIR / "ui"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "prabh.log"

load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

GROQ_MODEL = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.5-flash"

DEFAULT_MODE = "sunday"
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000


def has_groq() -> bool:
    return bool(GROQ_API_KEY)


def has_gemini() -> bool:
    return bool(GEMINI_API_KEY)