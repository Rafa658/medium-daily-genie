from __future__ import annotations

from datetime import datetime
from html import escape
from html import unescape

from src.medium_daily_digest.models import DigestArticle, DigestLink, DigestReport, EmailMessage
from src.medium_daily_digest.services.freedium_service import FreediumService
from src.medium_daily_digest.services.gmail_reader_service import GmailReaderService
from src.medium_daily_digest.services.ollama_summary_service import OllamaSummaryService
from src.medium_daily_digest.utils.link_extractor import (
    extract_digest_article_links_from_html,
    extract_links_from_html,
    extract_links_from_text,
)

START_MARKER = "Today's highlights"
END_MARKERS = (
    "See more of what you like and less of what you don't.",
    "See more of what you like and less of what you don’t.",
)


class DigestReportService:
    def __init__(
        self,
        gmail_reader: GmailReaderService | None = None,
        freedium_service: FreediumService | None = None,
        ollama_summary_service: OllamaSummaryService | None = None,
    ) -> None:
        self._gmail_reader = gmail_reader or GmailReaderService()
        self._freedium_service = freedium_service or FreediumService()
        self._ollama_summary_service = ollama_summary_service or OllamaSummaryService()

    def build_report(self) -> DigestReport:
        email_messages = self._gmail_reader.list_recent_messages()
        articles = self._build_articles(email_messages)
        return DigestReport(
            markdown=self._build_markdown(articles),
            html=self._build_html(articles),
        )

    def build_terminal_markdown(self) -> str:
        return self.build_report().markdown

    def _build_markdown(self, articles: list[DigestArticle]) -> str:
        lines = [self._build_title(), ""]

        if not articles:
            lines.append("_Nenhum email Medium Daily Digest encontrado no periodo._")
            return "\n".join(lines)

        for article in articles:
            lines.append(f"## {article.title}")
            lines.append(f"[Link Medium]({article.medium_url})")
            lines.append(self._build_summary_markdown(article))
            lines.append("")

        return "\n".join(lines).rstrip()

    def _build_html(self, articles: list[DigestArticle]) -> str:
        title = escape(self._build_title().replace("# ", "", 1))

        if not articles:
            return (
                "<html><body>"
                f"<h1>{title}</h1>"
                "<p><em>Nenhum email Medium Daily Digest encontrado no periodo.</em></p>"
                "</body></html>"
            )

        article_blocks = []
        for article in articles:
            article_blocks.append(
                "<section style=\"margin-bottom: 24px;\">"
                f"<h2 style=\"margin: 0 0 8px 0;\">{escape(article.title)}</h2>"
                f"<p style=\"margin: 0 0 6px 0;\"><a href=\"{escape(article.medium_url, quote=True)}\">"
                "Link Medium"
                "</a></p>"
                f"{self._build_summary_html(article)}"
                "</section>"
            )

        return (
            "<html><body style=\"font-family: Arial, sans-serif; line-height: 1.5;\">"
            f"<h1>{title}</h1>"
            f"{''.join(article_blocks)}"
            "</body></html>"
        )

    def _build_title(self) -> str:
        current_date = datetime.now().strftime("%d/%m/%Y")
        return f"# Medum Daily Digest - Dia {current_date}"

    def _build_articles(self, email_messages: list[EmailMessage]) -> list[DigestArticle]:
        articles: list[DigestArticle] = []
        for link in self._extract_links_from_messages(email_messages):
            article_html = self._freedium_service.get_article_html(link.url)
            articles.append(
                DigestArticle(
                    title=link.title,
                    medium_url=link.url,
                    ai_summary=self._ollama_summary_service.summarize_html(article_html)
                    if article_html
                    else None,
                )
            )

        return articles

    def _extract_links_from_messages(self, email_messages: list[EmailMessage]) -> list[DigestLink]:
        all_links: list[DigestLink] = []
        seen_urls: set[str] = set()

        for email_message in email_messages:
            message_links = self._extract_links_from_message(email_message)
            for link in message_links:
                if link.url in seen_urls:
                    continue
                seen_urls.add(link.url)
                all_links.append(link)

        return all_links

    def _extract_links_from_message(self, email_message: EmailMessage) -> list[DigestLink]:
        html_bodies = [body for body in email_message.bodies if "<html" in body.lower() or "<a " in body.lower()]
        for body in html_bodies:
            trimmed_body = self._trim_to_digest_section(body)
            if not trimmed_body:
                continue

            article_links = extract_digest_article_links_from_html(trimmed_body)
            if article_links:
                return article_links

        for body in email_message.bodies:
            trimmed_body = self._trim_to_digest_section(body)
            if not trimmed_body:
                continue

            links = self._extract_links(trimmed_body)
            if links:
                return links

        return []

    def _extract_links(self, body: str) -> list[DigestLink]:
        if "<html" in body.lower() or "<a " in body.lower():
            return extract_links_from_html(body)
        return extract_links_from_text(body)

    def _trim_to_digest_section(self, body: str) -> str:
        normalized_body = unescape(body)
        start_index = normalized_body.find(START_MARKER)
        if start_index == -1:
            return ""

        start_index += len(START_MARKER)
        end_index = len(normalized_body)

        for end_marker in END_MARKERS:
            candidate_index = normalized_body.find(end_marker, start_index)
            if candidate_index != -1:
                end_index = min(end_index, candidate_index)

        return normalized_body[start_index:end_index].strip()

    def _build_summary_markdown(self, article: DigestArticle) -> str:
        if article.ai_summary is None:
            return "_Resumo indisponivel no momento._"
        return article.ai_summary

    def _build_summary_html(self, article: DigestArticle) -> str:
        if article.ai_summary is None:
            return "<p style=\"margin: 0;\"><em>Resumo indisponivel no momento.</em></p>"

        paragraphs = []
        for block in article.ai_summary.split("\n\n"):
            stripped_block = block.strip()
            if not stripped_block:
                continue

            if stripped_block.startswith("## "):
                heading = stripped_block[3:].strip()
                paragraphs.append(f"<h3 style=\"margin: 16px 0 8px 0;\">{escape(heading)}</h3>")
                continue

            if stripped_block.startswith("**") and stripped_block.endswith("**"):
                heading = stripped_block.strip("*").strip()
                paragraphs.append(f"<h3 style=\"margin: 16px 0 8px 0;\">{escape(heading)}</h3>")
                continue

            if stripped_block.startswith("* "):
                items = [
                    f"<li>{escape(line[2:].strip())}</li>"
                    for line in stripped_block.splitlines()
                    if line.strip().startswith("* ")
                ]
                paragraphs.append(f"<ul style=\"margin: 8px 0 0 20px;\">{''.join(items)}</ul>")
                continue

            paragraphs.append(f"<p style=\"margin: 0 0 12px 0;\">{escape(stripped_block)}</p>")

        return "".join(paragraphs)
