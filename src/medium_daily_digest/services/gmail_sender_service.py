from __future__ import annotations

import base64
from email.message import EmailMessage

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.medium_daily_digest.config import (
    REPORT_EMAIL_CC,
    REPORT_EMAIL_RECIPIENT,
    REPORT_EMAIL_SENDER,
    REPORT_EMAIL_SUBJECT,
)
from src.medium_daily_digest.services.gmail_auth_service import GmailAuthService


class GmailSenderService:
    def __init__(self, auth_service: GmailAuthService | None = None) -> None:
        self._auth_service = auth_service or GmailAuthService()

    def send_report(self, markdown: str, html: str) -> None:
        try:
            service = build("gmail", "v1", credentials=self._auth_service.get_credentials())
            message = EmailMessage()
            message["To"] = ", ".join(REPORT_EMAIL_RECIPIENT)
            message["From"] = REPORT_EMAIL_SENDER
            message["Subject"] = REPORT_EMAIL_SUBJECT
            if REPORT_EMAIL_CC:
                message["Cc"] = ", ".join(REPORT_EMAIL_CC)
            message.set_content(markdown)
            message.add_alternative(html, subtype="html")

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            service.users().messages().send(userId="me", body={"raw": encoded_message}).execute()
        except RuntimeError:
            raise
        except HttpError as exc:
            raise RuntimeError(f"ERRO GMAIL: falha ao enviar o email de resumo. Detalhe: {exc}") from exc
