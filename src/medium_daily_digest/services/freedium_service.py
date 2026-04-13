from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.medium_daily_digest.config import FREEDIUM_BASE_URL, FREEDIUM_TIMEOUT_SECONDS


WORD_PATTERN = re.compile(r"\b\w+\b")


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_tag_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self._ignored_tag_stack and self._ignored_tag_stack[-1] == tag:
            self._ignored_tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._ignored_tag_stack:
            return
        self.parts.append(data)


class FreediumService:
    def get_html_word_count(self, medium_url: str) -> int | None:
        request_url = self._build_request_url(medium_url)
        request = Request(request_url, headers={"User-Agent": "medium-daily-genie/1.0"})

        try:
            with urlopen(request, timeout=FREEDIUM_TIMEOUT_SECONDS) as response:
                html = response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError):
            return None

        return self._count_visible_words(html)

    def _build_request_url(self, medium_url: str) -> str:
        encoded_url = quote(medium_url, safe=":/?&=%-._~")
        return f"{FREEDIUM_BASE_URL}/{encoded_url}"

    def _count_visible_words(self, html: str) -> int:
        parser = _VisibleTextParser()
        parser.feed(html)
        visible_text = " ".join(parser.parts)
        return len(WORD_PATTERN.findall(visible_text))
