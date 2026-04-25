from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from threading import Thread
from uuid import uuid4

from src.medium_daily_digest.services.digest_execution_service import DigestExecutionService
from src.medium_daily_digest.services.digest_preflight_service import DigestPreflightService
from src.medium_daily_digest.services.digest_run_store import DigestRunStore


app = FastAPI(title="Medium Daily Genie API")
run_store = DigestRunStore()


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/run_digest")
def run_digest() -> JSONResponse:
    started_at = datetime.now().astimezone().isoformat()
    active_job = run_store.get_active_job()
    if active_job is not None and active_job.get("status") in {"pending", "running"}:
        return JSONResponse(
            _build_conflict_response(active_job),
            status_code=409,
        )

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
                    "mode": "async",
                    "accepted": False,
                },
            },
            status_code=500,
        )

    run_store.create_job(request_id, started_at, services)
    thread = Thread(
        target=_execute_digest_job,
        args=(request_id, services),
        daemon=True,
    )
    thread.start()

    return JSONResponse(
        {
            "status": "ok",
            "message": "Digest iniciado com sucesso.",
            "request_id": request_id,
            "started_at": started_at,
            "services": services,
            "execution": {
                "mode": "async",
                "accepted": True,
            },
        },
        status_code=200,
    )


@app.get("/runs/{request_id}")
def get_run(request_id: str) -> JSONResponse:
    job = run_store.get_job(request_id)
    if job is None:
        return JSONResponse(
            {
                "status": "error",
                "message": "Execucao nao encontrada.",
                "request_id": request_id,
                "execution": {
                    "mode": "async",
                    "accepted": False,
                },
            },
            status_code=404,
        )

    return JSONResponse(_build_run_response(job, include_output=True), status_code=200)


def _apply_execution_errors(
    services: dict[str, dict[str, object]],
    output: str,
) -> dict[str, dict[str, object]]:
    updated_services = deepcopy(services)

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("Erro ao executar o prototipo:") or line.startswith("Erro inesperado ao executar o prototipo:"):
            updated_services["api"]["status"] = "error"
            updated_services["api"]["detail"] = line
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


def _execute_digest_job(
    request_id: str,
    initial_services: dict[str, dict[str, object]],
) -> None:
    run_store.mark_running(request_id)

    try:
        result = DigestExecutionService().run(
            on_output=lambda chunk: run_store.append_output(request_id, chunk)
        )
        services = _apply_execution_errors(initial_services, result.output)
        finished_at = datetime.now().astimezone().isoformat()
        message = (
            "Digest finalizado com sucesso."
            if result.success
            else "Falha durante a execucao do digest."
        )
        run_store.complete_job(
            request_id,
            success=result.success,
            message=message,
            services=services,
            finished_at=finished_at,
        )
    except Exception as exc:
        services = deepcopy(initial_services)
        services["api"]["status"] = "error"
        services["api"]["detail"] = f"Erro inesperado ao executar job em background: {exc}"
        run_store.append_output(
            request_id,
            f"Erro inesperado ao executar job em background: {exc}\n",
        )
        run_store.complete_job(
            request_id,
            success=False,
            message="Falha durante a execucao do digest.",
            services=services,
            finished_at=datetime.now().astimezone().isoformat(),
        )


def _build_conflict_response(active_job: dict[str, object]) -> dict[str, object]:
    execution = active_job.get("execution", {})
    if not isinstance(execution, dict):
        execution = {}

    response = {
        "status": "error",
        "message": "Ja existe um digest em andamento.",
        "request_id": active_job.get("request_id"),
        "started_at": active_job.get("started_at"),
        "services": active_job.get("services", {}),
        "execution": {
            "mode": execution.get("mode", "async"),
            "accepted": False,
        },
    }

    finished_at = active_job.get("finished_at")
    if isinstance(finished_at, str) and finished_at:
        response["finished_at"] = finished_at

    return response


def _build_run_response(
    job: dict[str, object],
    *,
    include_output: bool,
) -> dict[str, object]:
    execution = job.get("execution", {})
    if not isinstance(execution, dict):
        execution = {}

    response = {
        "status": job.get("status", "error"),
        "message": job.get("message", ""),
        "request_id": job.get("request_id"),
        "started_at": job.get("started_at"),
        "services": deepcopy(job.get("services", {})),
        "execution": {
            "mode": execution.get("mode", "async"),
            "accepted": execution.get("accepted", True),
        },
    }

    finished_at = job.get("finished_at")
    if isinstance(finished_at, str) and finished_at:
        response["finished_at"] = finished_at

    if include_output:
        response["execution"]["output"] = execution.get("output", "")

    return response
