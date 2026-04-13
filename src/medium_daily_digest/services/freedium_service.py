from __future__ import annotations

from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.medium_daily_digest.config import FREEDIUM_BASE_URL, FREEDIUM_TIMEOUT_SECONDS


class _MainContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.content_parts: list[str] = []
        self._capturing = False
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._capturing and tag == "div":
            class_value = dict(attrs).get("class", "")
            if class_value and "main-content" in class_value.split():
                self._capturing = True
                self._depth = 1
                self.content_parts.append(self.get_starttag_text())
                return

        if not self._capturing:
            return

        self._depth += 1
        self.content_parts.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        if not self._capturing:
            return

        self.content_parts.append(f"</{tag}>")
        self._depth -= 1
        if self._depth == 0:
            self._capturing = False

    def handle_data(self, data: str) -> None:
        if self._capturing:
            self.content_parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._capturing:
            self.content_parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._capturing:
            self.content_parts.append(f"&#{name};")

    def extracted_html(self) -> str:
        return "".join(self.content_parts).strip()


class FreediumService:
    def get_article_html(self, medium_url: str) -> str | None:
        request_url = self._build_request_url(medium_url)
        request = Request(request_url, headers={"User-Agent": "medium-daily-genie/1.0"})

        try:
            with urlopen(request, timeout=FREEDIUM_TIMEOUT_SECONDS) as response:
                html = response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError):
            return None

        return self._extract_article_html(html) or html

    def _build_request_url(self, medium_url: str) -> str:
        encoded_url = quote(medium_url, safe=":/?&=%-._~")
        return f"{FREEDIUM_BASE_URL}/{encoded_url}"

    def _extract_article_html(self, html: str) -> str:
        parser = _MainContentParser()
        parser.feed(html)
        return parser.extracted_html()
