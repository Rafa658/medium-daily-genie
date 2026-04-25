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


def _get_env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


def _get_env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


def _get_env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized_value = raw_value.strip().lower()
    if normalized_value in {"1", "true", "yes", "on"}:
        return True
    if normalized_value in {"0", "false", "no", "off"}:
        return False
    return default


def _get_env_list(name: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    values = tuple(
        item.strip()
        for item in raw_value.split(",")
        if item.strip()
    )
    return values or default


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
REPORT_EMAIL_CC = _get_env_list(
    "MEDIUM_DAILY_GENIE_REPORT_EMAIL_CC",
    (),
)
FREEDIUM_BASE_URL = _get_env("MEDIUM_DAILY_GENIE_FREEDIUM_BASE_URL", "http://127.0.0.1:7080")
FREEDIUM_TIMEOUT_SECONDS = 60
LLM_PROVIDER = _get_env("MDG_LLM_PROVIDER", "ollama")
LLM_BASE_URL = _get_env("MDG_LLM_BASE_URL", "http://127.0.0.1:11434")
LLM_MODEL = _get_env("MDG_LLM_MODEL", "gemma3:4b")
LLM_ENDPOINT_PATH = _get_env("MDG_LLM_ENDPOINT_PATH", "/api/generate")
LLM_API_KEY = _get_env("MDG_LLM_API_KEY", "")
LLM_RESPONSE_FIELD = _get_env("MDG_LLM_RESPONSE_FIELD", "response")
LLM_TIMEOUT_SECONDS = _get_env_int("MDG_LLM_TIMEOUT_SECONDS", 180)
LLM_THINK = _get_env_bool("MDG_LLM_THINK", False)
LLM_TEMPERATURE = _get_env_float("MDG_LLM_TEMPERATURE", 0.1)
SERVICE_CHECK_TIMEOUT_SECONDS = _get_env_int("MDG_SERVICE_CHECK_TIMEOUT_SECONDS", 100)
SUMMARIZE_PROMPT_FILE = BASE_DIR / "summarize.md"


def resolve_google_client_secret_file() -> Path:
    if DEFAULT_GOOGLE_CLIENT_SECRET_FILE.exists():
        return DEFAULT_GOOGLE_CLIENT_SECRET_FILE

    root_candidates = sorted(BASE_DIR.glob("client_secret_*.json"))
    if root_candidates:
        return root_candidates[0]

    return DEFAULT_GOOGLE_CLIENT_SECRET_FILE
