from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from src.medium_daily_digest.config import (
    GMAIL_SCOPES,
    GOOGLE_TOKEN_FILE,
    resolve_google_client_secret_file,
)


class GmailAuthService:
    def get_credentials(self) -> Credentials:
        client_secret_file = resolve_google_client_secret_file()
        credentials = self._load_saved_credentials()
        if credentials and not credentials.has_scopes(GMAIL_SCOPES):
            credentials = None

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._persist_credentials(credentials)
            return credentials

        if credentials and credentials.valid:
            return credentials

        if not client_secret_file.exists():
            raise RuntimeError(self._missing_credentials_message(client_secret_file))

        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_file,
            GMAIL_SCOPES,
        )
        credentials = flow.run_local_server(port=0)
        self._persist_credentials(credentials)
        return credentials

    def _load_saved_credentials(self) -> Credentials | None:
        if not GOOGLE_TOKEN_FILE.exists():
            return None

        return Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), GMAIL_SCOPES)

    def _persist_credentials(self, credentials: Credentials) -> None:
        GOOGLE_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        GOOGLE_TOKEN_FILE.write_text(credentials.to_json())

    @staticmethod
    def _missing_credentials_message(credentials_path: Path) -> str:
        return (
            "Arquivo de credenciais OAuth do Google nao encontrado.\n"
            f"Esperado em: {credentials_path}\n"
            "Crie um OAuth Client ID do tipo Desktop App no Google Cloud Console, "
            "ative a Gmail API e salve o JSON nesse caminho."
        )
