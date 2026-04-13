from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.medium_daily_digest.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    SUMMARIZE_PROMPT_FILE,
)


class _ArticleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_tag_stack.append(tag)
            return

        if tag in {"p", "h1", "h2", "h3", "h4", "li", "blockquote"}:
            self.parts.append("\n\n")

    def handle_endtag(self, tag: str) -> None:
        if self._ignored_tag_stack and self._ignored_tag_stack[-1] == tag:
            self._ignored_tag_stack.pop()
            return

        if tag in {"p", "h1", "h2", "h3", "h4", "li", "blockquote"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_tag_stack:
            return

        stripped_data = data.strip()
        if stripped_data:
            self.parts.append(stripped_data)
            self.parts.append(" ")

    def extracted_text(self) -> str:
        text = "".join(self.parts)
        lines = [line.strip() for line in text.splitlines()]
        compact_lines = [line for line in lines if line]
        return "\n".join(compact_lines).strip()


class OllamaSummaryService:
    def __init__(self, prompt_file: Path | None = None) -> None:
        self._prompt_file = prompt_file or SUMMARIZE_PROMPT_FILE
        self._prompt = self._prompt_file.read_text(encoding="utf-8").strip()

    def summarize_html(self, html: str) -> str | None:
        article_text = self._extract_text_from_html(html)
        if not article_text:
            return None

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": self._build_prompt(article_text),
            "stream": False,
        }
        request = Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
                body = json.loads(response.read().decode("utf-8", errors="replace"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return None

        summary = body.get("response", "")
        cleaned_summary = summary.strip()
        return cleaned_summary or None

    def _build_prompt(self, article_text: str) -> str:
        return (
            f"{self._prompt}\n\n"
            "O texto abaixo foi extraido do HTML de um artigo do Medium.\n"
            "Produza o resumo final seguindo rigorosamente as instrucoes acima.\n\n"
            "Texto do artigo a resumir:\n"
            f"{article_text}"
        )

    def _extract_text_from_html(self, html: str) -> str:
        parser = _ArticleTextParser()
        parser.feed(html)
        return parser.extracted_text()
