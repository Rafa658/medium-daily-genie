from dataclasses import dataclass


@dataclass(frozen=True)
class DigestLink:
    title: str
    url: str


@dataclass(frozen=True)
class EmailMessage:
    subject: str
    bodies: tuple[str, ...]


@dataclass(frozen=True)
class DigestReport:
    markdown: str
    html: str
