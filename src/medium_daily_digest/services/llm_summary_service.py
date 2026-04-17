from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.medium_daily_digest.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_ENDPOINT_PATH,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_RESPONSE_FIELD,
    LLM_TEMPERATURE,
    LLM_THINK,
    LLM_TIMEOUT_SECONDS,
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


class LlmSummaryService:
    def __init__(self, prompt_file: Path | None = None) -> None:
        self._prompt_file = prompt_file or SUMMARIZE_PROMPT_FILE
        self._prompt = self._prompt_file.read_text(encoding="utf-8").strip()

    def summarize_html(self, html: str) -> str | None:
        article_text = self._extract_text_from_html(html)
        if not article_text:
            return None

        return self._generate_summary(article_text)

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

    def _generate_summary(self, article_text: str) -> str | None:
        if LLM_PROVIDER == "gemini":
            return self._generate_gemini_summary(article_text)

        return self._generate_generic_summary(article_text)

    def _generate_generic_summary(self, article_text: str) -> str | None:
        payload = {
            "model": LLM_MODEL,
            "prompt": self._build_prompt(article_text),
            "stream": False,
            "options": {
                "temperature": LLM_TEMPERATURE,
            },
        }
        if LLM_THINK:
            payload["think"] = True

        request = Request(
            self._build_request_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=LLM_TIMEOUT_SECONDS) as response:
                body = json.loads(response.read().decode("utf-8", errors="replace"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return None

        summary = body.get(LLM_RESPONSE_FIELD, "")
        if not isinstance(summary, str):
            return None

        cleaned_summary = summary.strip()
        return cleaned_summary or None

    def _generate_gemini_summary(self, article_text: str) -> str | None:
        if not LLM_API_KEY:
            return None

        payload = {
            "systemInstruction": {
                "parts": [{"text": self._prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": self._build_gemini_user_content(article_text)}],
                }
            ],
            "generationConfig": {
                "temperature": LLM_TEMPERATURE,
            },
        }

        request = Request(
            self._build_gemini_request_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=LLM_TIMEOUT_SECONDS) as response:
                body = json.loads(response.read().decode("utf-8", errors="replace"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return None

        return self._extract_gemini_text(body)

    def _build_gemini_user_content(self, article_text: str) -> str:
        return (
            "O texto abaixo foi extraido do HTML de um artigo do Medium.\n"
            "Produza o resumo final seguindo rigorosamente as instrucoes de sistema.\n\n"
            "Texto do artigo a resumir:\n"
            f"{article_text}"
        )

    def _extract_gemini_text(self, body: dict[str, object]) -> str | None:
        candidates = body.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            return None

        first_candidate = candidates[0]
        if not isinstance(first_candidate, dict):
            return None

        content = first_candidate.get("content")
        if not isinstance(content, dict):
            return None

        parts = content.get("parts")
        if not isinstance(parts, list):
            return None

        text_parts: list[str] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                text_parts.append(text.strip())

        if not text_parts:
            return None

        return "\n".join(text_parts).strip() or None

    def _build_request_url(self) -> str:
        endpoint_path = LLM_ENDPOINT_PATH.replace("{model}", LLM_MODEL)
        return f"{LLM_BASE_URL.rstrip('/')}/{endpoint_path.lstrip('/')}"

    def _build_gemini_request_url(self) -> str:
        query = urlencode({"key": LLM_API_KEY})
        return f"{self._build_request_url()}?{query}"