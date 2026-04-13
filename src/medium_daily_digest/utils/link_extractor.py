from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from typing import List
from urllib.parse import urlsplit, urlunsplit

from src.medium_daily_digest.models import DigestLink


URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[DigestLink] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return

        href = dict(attrs).get("href")
        if not href:
            return

        self._current_href = href.strip()
        self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is None:
            return
        self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._current_href is None:
            return

        title = " ".join(part.strip() for part in self._current_text if part.strip())
        title = title or self._current_href
        self.links.append(DigestLink(title=title, url=self._current_href))
        self._current_href = None
        self._current_text = []


class _DigestArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[DigestLink] = []
        self._current_href: str | None = None
        self._anchor_depth = 0
        self._inside_h2 = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._current_href = href.strip()
                self._anchor_depth = 1
                self._title_parts = []
                self._inside_h2 = False
            return

        if self._current_href is None:
            return

        self._anchor_depth += 1
        if tag == "h2":
            self._inside_h2 = True

    def handle_data(self, data: str) -> None:
        if self._current_href is None or not self._inside_h2:
            return
        self._title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._current_href is None:
            return

        if tag == "h2":
            self._inside_h2 = False

        self._anchor_depth -= 1
        if self._anchor_depth > 0:
            return

        title = " ".join(part.strip() for part in self._title_parts if part.strip())
        normalized_url = normalize_url(self._current_href)
        if title and _looks_like_medium_article(normalized_url):
            self.links.append(DigestLink(title=title, url=normalized_url))

        self._current_href = None
        self._title_parts = []
        self._inside_h2 = False
        self._anchor_depth = 0


def extract_links_from_html(html: str) -> list[DigestLink]:
    parser = _AnchorParser()
    parser.feed(html)
    return _deduplicate(parser.links)


def extract_digest_article_links_from_html(html: str) -> list[DigestLink]:
    parser = _DigestArticleParser()
    parser.feed(unescape(html))
    return _deduplicate(parser.links)


def extract_links_from_text(text: str) -> list[DigestLink]:
    links = [DigestLink(title=match, url=normalize_url(match)) for match in URL_PATTERN.findall(text)]
    return _deduplicate(links)


def _deduplicate(links: list[DigestLink]) -> list[DigestLink]:
    unique_links: list[DigestLink] = []
    seen_urls: set[str] = set()

    for link in links:
        if link.url in seen_urls:
            continue
        seen_urls.add(link.url)
        unique_links.append(link)

    return unique_links


def normalize_url(url: str) -> str:
    cleaned = url.strip().rstrip(").,;")
    parts = urlsplit(cleaned)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _looks_like_medium_article(url: str) -> bool:
    parts = urlsplit(url)
    if "medium.com" not in parts.netloc:
        return False

    segments = [segment for segment in parts.path.split("/") if segment]
    return len(segments) >= 2
