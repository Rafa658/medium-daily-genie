from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.medium_daily_digest.config import (
    FREEDIUM_BASE_URL,
    LLM_MODEL,
    LLM_PROVIDER,
    SERVICE_CHECK_TIMEOUT_SECONDS,
)
from src.medium_daily_digest.services.gmail_auth_service import GmailAuthService
from src.medium_daily_digest.services.llm_summary_service import LlmSummaryService


class DigestPreflightService:
    def __init__(
        self,
        gmail_auth_service: GmailAuthService | None = None,
        llm_summary_service: LlmSummaryService | None = None,
    ) -> None:
        self._gmail_auth_service = gmail_auth_service or GmailAuthService()
        self._llm_summary_service = llm_summary_service or LlmSummaryService()

    def run_checks(self) -> dict[str, dict[str, object]]:
        return {
            "api": {
                "status": "ok",
                "detail": "Requisicao recebida e processada pela API.",
            },
            "gmail": self._check_gmail(),
            "freedium": self._check_freedium(),
            "llm": self._check_llm(),
        }

    def _check_gmail(self) -> dict[str, object]:
        try:
            service = build("gmail", "v1", credentials=self._gmail_auth_service.get_credentials())
            profile = service.users().getProfile(userId="me").execute()
        except RuntimeError as exc:
            return {
                "status": "error",
                "detail": str(exc),
            }
        except HttpError as exc:
            return {
                "status": "error",
                "detail": f"ERRO GMAIL: falha ao consultar a API do Gmail. Detalhe: {exc}",
            }

        email_address = profile.get("emailAddress", "desconhecido")
        return {
            "status": "ok",
            "detail": f"Autenticacao valida e leitura de emails disponivel para {email_address}.",
        }

    def _check_freedium(self) -> dict[str, object]:
        request = Request(FREEDIUM_BASE_URL, headers={"User-Agent": "medium-daily-genie/1.0"})

        try:
            with urlopen(request, timeout=SERVICE_CHECK_TIMEOUT_SECONDS) as response:
                status = getattr(response, "status", 200)
        except HTTPError as exc:
            return {
                "status": "error",
                "detail": f"ERRO FREEDIUM: requisicao rejeitada (HTTP {exc.code}).",
            }
        except URLError as exc:
            return {
                "status": "error",
                "detail": f"ERRO FREEDIUM: falha ao acessar {FREEDIUM_BASE_URL}. Detalhe: {exc.reason}",
            }
        except TimeoutError:
            return {
                "status": "error",
                "detail": "ERRO FREEDIUM: timeout ao aguardar resposta do servico.",
            }

        if not 200 <= status < 300:
            return {
                "status": "error",
                "detail": f"ERRO FREEDIUM: servico respondeu com status {status}.",
            }

        return {
            "status": "ok",
            "detail": f"Servico acessivel e retornando HTML (status {status}).",
        }

    def _check_llm(self) -> dict[str, object]:
        result = self._llm_summary_service.summarize_html(
            "<html><body><h1>Teste</h1><p>Resuma este texto curto.</p></body></html>"
        )
        if result.startswith("ERRO "):
            return {
                "status": "error",
                "provider": LLM_PROVIDER,
                "model": LLM_MODEL,
                "detail": result,
            }

        return {
            "status": "ok",
            "provider": LLM_PROVIDER,
            "model": LLM_MODEL,
            "detail": "Servico acessivel e apto a gerar resumos.",
        }
