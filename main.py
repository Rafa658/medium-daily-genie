from src.medium_daily_digest.services.digest_report_service import DigestReportService
from src.medium_daily_digest.services.gmail_sender_service import GmailSenderService


def main() -> None:
    try:
        report_service = DigestReportService()
        report = report_service.build_report()
        print(report.markdown)

        sender_service = GmailSenderService()
        sender_service.send_report(report.markdown, report.html)
    except RuntimeError as exc:
        print(f"Erro ao executar o prototipo:\n{exc}")


if __name__ == "__main__":
    main()
