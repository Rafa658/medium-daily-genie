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

    def summarize_html(self, html: str) -> str:
        article_text = self._extract_text_from_html(html)
        if not article_text:
            error_message = "ERRO LLM: nao foi possivel extrair texto legivel do HTML do artigo."
            print(error_message)
            return error_message

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

    def _generate_summary(self, article_text: str) -> str:
        if LLM_PROVIDER == "gemini":
            return self._generate_gemini_summary(article_text)

        return self._generate_generic_summary(article_text)

    def _generate_generic_summary(self, article_text: str) -> str:
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
        except HTTPError as exc:
            return self._http_error_message("LLM", exc)
        except URLError as exc:
            return self._network_error_message("LLM", exc)
        except TimeoutError:
            return self._timeout_error_message("LLM")
        except json.JSONDecodeError as exc:
            error_message = f"ERRO LLM: resposta da API nao veio em JSON valido. Detalhe: {exc}"
            print(error_message)
            return error_message

        summary = body.get(LLM_RESPONSE_FIELD, "")
        if not isinstance(summary, str):
            error_message = (
                "ERRO LLM: resposta da API nao contem o campo de texto esperado "
                f"('{LLM_RESPONSE_FIELD}')."
            )
            print(error_message)
            return error_message

        cleaned_summary = summary.strip()
        if cleaned_summary:
            return cleaned_summary

        error_message = "ERRO LLM: a resposta da API veio vazia."
        print(error_message)
        return error_message

    def _generate_gemini_summary(self, article_text: str) -> str:
        if not LLM_API_KEY:
            error_message = "ERRO GEMINI: chave de API ausente. Defina MDG_LLM_API_KEY no ambiente."
            print(error_message)
            return error_message

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
        except HTTPError as exc:
            return self._http_error_message("GEMINI", exc)
        except URLError as exc:
            return self._network_error_message("GEMINI", exc)
        except TimeoutError:
            return self._timeout_error_message("GEMINI")
        except json.JSONDecodeError as exc:
            error_message = f"ERRO GEMINI: resposta da API nao veio em JSON valido. Detalhe: {exc}"
            print(error_message)
            return error_message

        return self._extract_gemini_text(body)

    def _build_gemini_user_content(self, article_text: str) -> str:
        return (
            "O texto abaixo foi extraido do HTML de um artigo do Medium.\n"
            "Produza o resumo final seguindo rigorosamente as instrucoes de sistema.\n\n"
            "Texto do artigo a resumir:\n"
            f"{article_text}"
        )

    def _extract_gemini_text(self, body: dict[str, object]) -> str:
        candidates = body.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            error_message = self._gemini_response_error_message(body)
            print(error_message)
            return error_message

        first_candidate = candidates[0]
        if not isinstance(first_candidate, dict):
            error_message = "ERRO GEMINI: resposta da LLM veio em formato inesperado (candidate invalido)."
            print(error_message)
            return error_message

        content = first_candidate.get("content")
        if not isinstance(content, dict):
            error_message = "ERRO GEMINI: resposta da LLM nao contem content no formato esperado."
            print(error_message)
            return error_message

        parts = content.get("parts")
        if not isinstance(parts, list):
            error_message = "ERRO GEMINI: resposta da LLM nao contem parts no formato esperado."
            print(error_message)
            return error_message

        text_parts: list[str] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                text_parts.append(text.strip())

        if not text_parts:
            error_message = self._gemini_response_error_message(body)
            print(error_message)
            return error_message

        cleaned_summary = "\n".join(text_parts).strip()
        if cleaned_summary:
            return cleaned_summary

        error_message = "ERRO GEMINI: resposta da LLM veio vazia."
        print(error_message)
        return error_message

    def _build_request_url(self) -> str:
        endpoint_path = LLM_ENDPOINT_PATH.replace("{model}", LLM_MODEL)
        return f"{LLM_BASE_URL.rstrip('/')}/{endpoint_path.lstrip('/')}"

    def _build_gemini_request_url(self) -> str:
        query = urlencode({"key": LLM_API_KEY})
        return f"{self._build_request_url()}?{query}"

    def _http_error_message(self, provider_name: str, exc: HTTPError) -> str:
        detail = exc.reason
        try:
            response_body = exc.read().decode("utf-8", errors="replace").strip()
            if response_body:
                detail = response_body
        except Exception:
            pass

        error_message = (
            f"ERRO {provider_name}: requisicao rejeitada pela API "
            f"(HTTP {exc.code}). Detalhe: {detail}"
        )
        print(error_message)
        return error_message

    def _network_error_message(self, provider_name: str, exc: URLError) -> str:
        error_message = f"ERRO {provider_name}: falha de rede ao chamar a API. Detalhe: {exc.reason}"
        print(error_message)
        return error_message

    def _timeout_error_message(self, provider_name: str) -> str:
        error_message = f"ERRO {provider_name}: timeout ao aguardar resposta da API."
        print(error_message)
        return error_message

    def _gemini_response_error_message(self, body: dict[str, object]) -> str:
        prompt_feedback = body.get("promptFeedback")
        if isinstance(prompt_feedback, dict):
            block_reason = prompt_feedback.get("blockReason")
            if isinstance(block_reason, str) and block_reason:
                return f"ERRO GEMINI: resposta bloqueada pela API. Motivo: {block_reason}"

        return "ERRO GEMINI: resposta da LLM nao contem texto resumido no formato esperado."
