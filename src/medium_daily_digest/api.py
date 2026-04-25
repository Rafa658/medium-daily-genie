from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from uuid import uuid4

from src.medium_daily_digest.services.digest_execution_service import DigestExecutionService
from src.medium_daily_digest.services.digest_preflight_service import DigestPreflightService


app = FastAPI(title="Medium Daily Genie API")


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/run_digest")
def run_digest() -> JSONResponse:
    started_at = datetime.now().astimezone().isoformat()
    request_id = f"{started_at}__{uuid4().hex[:6]}"
    services = DigestPreflightService().run_checks()
    has_preflight_errors = any(
        service["status"] == "error"
        for service in services.values()
    )
    if has_preflight_errors:
        return JSONResponse(
            {
                "status": "error",
                "message": "Falha ao iniciar o digest.",
                "request_id": request_id,
                "started_at": started_at,
                "services": services,
                "execution": {
                    "mode": "sync",
                    "accepted": False,
                },
            },
            status_code=500,
        )

    result = DigestExecutionService().run()
    services = _apply_execution_errors(services, result.output)
    status_code = 200 if result.success else 500
    return JSONResponse(
        {
            "status": "ok" if result.success else "error",
            "message": (
                "Digest executado com sucesso."
                if result.success
                else "Falha durante a execucao do digest."
            ),
            "request_id": request_id,
            "started_at": started_at,
            "services": services,
            "execution": {
                "mode": "sync",
                "accepted": result.success,
            },
        },
        status_code=status_code,
    )


def _apply_execution_errors(
    services: dict[str, dict[str, object]],
    output: str,
) -> dict[str, dict[str, object]]:
    updated_services = deepcopy(services)

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if "ERRO GMAIL:" in line:
            updated_services["gmail"]["status"] = "error"
            updated_services["gmail"]["detail"] = line
            continue

        if "ERRO FREEDIUM:" in line:
            updated_services["freedium"]["status"] = "error"
            updated_services["freedium"]["detail"] = line
            continue

        if "ERRO GEMINI:" in line or "ERRO LLM:" in line:
            updated_services["llm"]["status"] = "error"
            updated_services["llm"]["detail"] = line

    return updated_services
