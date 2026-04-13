from __future__ import annotations

import base64
from email.header import decode_header, make_header
from typing import Any

from googleapiclient.discovery import build

from src.medium_daily_digest.config import (
    LOOKBACK_DAYS,
    MEDIUM_FROM_DISPLAY,
    MEDIUM_FROM_EMAIL,
)
from src.medium_daily_digest.models import EmailMessage
from src.medium_daily_digest.services.gmail_auth_service import GmailAuthService


class GmailReaderService:
    def __init__(self, auth_service: GmailAuthService | None = None) -> None:
        self._auth_service = auth_service or GmailAuthService()

    def list_recent_messages(self) -> list[EmailMessage]:
        service = build("gmail", "v1", credentials=self._auth_service.get_credentials())
        query = f"newer_than:{LOOKBACK_DAYS}d from:{MEDIUM_FROM_EMAIL}"
        messages = self._list_all_messages(service, query)

        email_messages: list[EmailMessage] = []
        for message in messages:
            payload = (
                service.users()
                .messages()
                .get(userId="me", id=message["id"], format="full")
                .execute()
            )

            sender = self._extract_header(payload, "from")
            if not self._is_medium_sender(sender):
                continue

            subject = self._extract_subject(payload)
            bodies = tuple(self._extract_message_bodies(payload))
            email_messages.append(EmailMessage(subject=subject or "(Sem assunto)", bodies=bodies))

        return email_messages

    def _list_all_messages(self, service: Any, query: str) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        next_page_token: str | None = None

        while True:
            response = (
                service.users()
                .messages()
                .list(userId="me", q=query, pageToken=next_page_token)
                .execute()
            )
            messages.extend(response.get("messages", []))
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                return messages

    def _extract_subject(self, message: dict[str, Any]) -> str:
        return self._extract_header(message, "subject")

    def _extract_header(self, message: dict[str, Any], header_name: str) -> str:
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name", "").lower() != header_name.lower():
                continue
            raw_value = header.get("value", "")
            return str(make_header(decode_header(raw_value)))
        return ""

    def _extract_message_bodies(self, message: dict[str, Any]) -> list[str]:
        payload = message.get("payload", {})
        contents: list[str] = []
        self._collect_bodies(payload, contents)
        return contents

    def _collect_bodies(self, payload: dict[str, Any], contents: list[str]) -> None:
        body = payload.get("body", {})
        data = body.get("data")
        mime_type = payload.get("mimeType", "")

        if data and mime_type in {"text/html", "text/plain"}:
            contents.append(self._decode_base64url(data))

        for part in payload.get("parts", []):
            self._collect_bodies(part, contents)

    @staticmethod
    def _decode_base64url(content: str) -> str:
        padding = "=" * (-len(content) % 4)
        decoded = base64.urlsafe_b64decode(content + padding)
        return decoded.decode("utf-8", errors="replace")

    @staticmethod
    def _is_medium_sender(sender: str) -> bool:
        normalized_sender = sender.strip().lower()
        return normalized_sender in {
            MEDIUM_FROM_DISPLAY.lower(),
            MEDIUM_FROM_EMAIL.lower(),
        }
