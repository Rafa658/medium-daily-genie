from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse

from src.medium_daily_digest.services.digest_execution_service import DigestExecutionService


app = FastAPI(title="Medium Daily Genie API")


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/run_digest")
def run_digest() -> PlainTextResponse:
    result = DigestExecutionService().run()
    status_code = 200 if result.success else 500
    return PlainTextResponse(result.output, status_code=status_code)
