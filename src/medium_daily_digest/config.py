from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
CREDENTIALS_DIR = BASE_DIR / "credentials"
DEFAULT_GOOGLE_CLIENT_SECRET_FILE = CREDENTIALS_DIR / "google_oauth_client.json"
GOOGLE_TOKEN_FILE = CREDENTIALS_DIR / "token.json"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
LOOKBACK_DAYS = 1
MEDIUM_FROM_EMAIL = "noreply@medium.com"
MEDIUM_FROM_DISPLAY = "Medium Daily Digest <noreply@medium.com>"
REPORT_EMAIL_SUBJECT = "Resumo diário Medium"
REPORT_EMAIL_RECIPIENT = "vrafagamer@gmail.com"
REPORT_EMAIL_SENDER = "Medium Daily Genie <vrafagamer@gmail.com>"
FREEDIUM_BASE_URL = "http://192.168.15.7:7080"
FREEDIUM_TIMEOUT_SECONDS = 60


def resolve_google_client_secret_file() -> Path:
    if DEFAULT_GOOGLE_CLIENT_SECRET_FILE.exists():
        return DEFAULT_GOOGLE_CLIENT_SECRET_FILE

    root_candidates = sorted(BASE_DIR.glob("client_secret_*.json"))
    if root_candidates:
        return root_candidates[0]

    return DEFAULT_GOOGLE_CLIENT_SECRET_FILE
