from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO

from src.medium_daily_digest.models import DigestExecutionResult
from src.medium_daily_digest.services.digest_report_service import DigestReportService
from src.medium_daily_digest.services.gmail_sender_service import GmailSenderService


class DigestExecutionService:
    def __init__(
        self,
        report_service: DigestReportService | None = None,
        sender_service: GmailSenderService | None = None,
    ) -> None:
        self._report_service = report_service or DigestReportService()
        self._sender_service = sender_service or GmailSenderService()

    def run(self) -> DigestExecutionResult:
        buffer = StringIO()
        success = True

        with redirect_stdout(buffer):
            try:
                report = self._report_service.build_report()
                print(report.markdown)
                self._sender_service.send_report(report.markdown, report.html)
            except RuntimeError as exc:
                success = False
                print(f"Erro ao executar o prototipo:\n{exc}")

        output = buffer.getvalue()
        print(output, end="")
        return DigestExecutionResult(success=success, output=output)
