from dataclasses import dataclass


@dataclass(frozen=True)
class DigestLink:
    title: str
    url: str


@dataclass(frozen=True)
class DigestArticle:
    title: str
    medium_url: str
    ai_summary: str | None


@dataclass(frozen=True)
class EmailMessage:
    subject: str
    bodies: tuple[str, ...]


@dataclass(frozen=True)
class DigestReport:
    markdown: str
    html: str


@dataclass(frozen=True)
class DigestExecutionResult:
    success: bool
    output: str
