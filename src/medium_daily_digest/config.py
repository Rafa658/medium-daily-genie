import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
CREDENTIALS_DIR = BASE_DIR / "credentials"
DEFAULT_GOOGLE_CLIENT_SECRET_FILE = CREDENTIALS_DIR / "google_oauth_client.json"
GOOGLE_TOKEN_FILE = CREDENTIALS_DIR / "token.json"
ENV_FILE = BASE_DIR / ".env"


def _load_dotenv() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


_load_dotenv()

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
LOOKBACK_DAYS = 1
MEDIUM_FROM_EMAIL = "noreply@medium.com"
MEDIUM_FROM_DISPLAY = "Medium Daily Digest <noreply@medium.com>"
REPORT_EMAIL_SUBJECT = "Resumo diário Medium"
REPORT_EMAIL_RECIPIENT = _get_env("MEDIUM_DAILY_GENIE_REPORT_EMAIL_RECIPIENT", "placeholder@example.com")
REPORT_EMAIL_SENDER = _get_env(
    "MEDIUM_DAILY_GENIE_REPORT_EMAIL_SENDER",
    "Medium Daily Genie <placeholder@example.com>",
)
FREEDIUM_BASE_URL = _get_env("MEDIUM_DAILY_GENIE_FREEDIUM_BASE_URL", "http://127.0.0.1:7080")
FREEDIUM_TIMEOUT_SECONDS = 60
OLLAMA_BASE_URL = _get_env("MEDIUM_DAILY_GENIE_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = _get_env("MEDIUM_DAILY_GENIE_OLLAMA_MODEL", "gemma3:4b")
OLLAMA_TIMEOUT_SECONDS = 180
OLLAMA_THINK = False
OLLAMA_TEMPERATURE = 0.1
SUMMARIZE_PROMPT_FILE = BASE_DIR / "summarize.md"


def resolve_google_client_secret_file() -> Path:
    if DEFAULT_GOOGLE_CLIENT_SECRET_FILE.exists():
        return DEFAULT_GOOGLE_CLIENT_SECRET_FILE

    root_candidates = sorted(BASE_DIR.glob("client_secret_*.json"))
    if root_candidates:
        return root_candidates[0]

    return DEFAULT_GOOGLE_CLIENT_SECRET_FILE
