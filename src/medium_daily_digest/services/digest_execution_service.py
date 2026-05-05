from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from typing import Callable
import traceback

from src.medium_daily_digest.models import DigestExecutionResult
from src.medium_daily_digest.services.digest_report_service import DigestReportService
from src.medium_daily_digest.services.gmail_sender_service import GmailSenderService


class _StreamingBuffer:
    def __init__(self, on_output: Callable[[str], None] | None = None) -> None:
        self._buffer = StringIO()
        self._on_output = on_output

    def write(self, text: str) -> int:
        written = self._buffer.write(text)
        if self._on_output is not None and text:
            self._on_output(text)
        return written

    def flush(self) -> None:
        return None

    def getvalue(self) -> str:
        return self._buffer.getvalue()


class DigestExecutionService:
    def __init__(
        self,
        report_service: DigestReportService | None = None,
        sender_service: GmailSenderService | None = None,
    ) -> None:
        self._report_service = report_service or DigestReportService()
        self._sender_service = sender_service or GmailSenderService()

    def run(self, on_output: Callable[[str], None] | None = None) -> DigestExecutionResult:
        buffer = _StreamingBuffer(on_output=on_output)
        success = True

        with redirect_stdout(buffer):
            try:
                report = self._report_service.build_report()
                print("Relatorio gerado com sucesso. Enviando por email...")
                self._sender_service.send_report(report.markdown, report.html)
                print("Email enviado com sucesso.")
            except RuntimeError as exc:
                success = False
                print(f"Erro ao executar o prototipo:\n{exc}")
            except Exception:
                success = False
                print("Erro inesperado ao executar o prototipo:")
                print(traceback.format_exc())

        output = buffer.getvalue()
        print(output, end="")
        return DigestExecutionResult(success=success, output=output)
