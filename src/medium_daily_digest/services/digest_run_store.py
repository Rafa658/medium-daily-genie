from __future__ import annotations

from copy import deepcopy
from threading import Lock


class DigestRunStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: dict[str, dict[str, object]] = {}
        self._active_request_id: str | None = None

    def get_job(self, request_id: str) -> dict[str, object] | None:
        with self._lock:
            job = self._jobs.get(request_id)
            return deepcopy(job) if job is not None else None

    def get_active_job(self) -> dict[str, object] | None:
        with self._lock:
            if self._active_request_id is None:
                return None

            job = self._jobs.get(self._active_request_id)
            return deepcopy(job) if job is not None else None

    def create_job(
        self,
        request_id: str,
        started_at: str,
        services: dict[str, dict[str, object]],
    ) -> dict[str, object]:
        with self._lock:
            job = {
                "status": "pending",
                "message": "Digest aguardando execucao.",
                "request_id": request_id,
                "started_at": started_at,
                "finished_at": None,
                "services": deepcopy(services),
                "execution": {
                    "mode": "async",
                    "accepted": True,
                    "output": "",
                },
            }
            self._jobs[request_id] = job
            self._active_request_id = request_id
            return deepcopy(job)

    def mark_running(self, request_id: str) -> None:
        with self._lock:
            job = self._jobs.get(request_id)
            if job is None:
                return

            job["status"] = "running"
            job["message"] = "Digest em execucao."

    def append_output(self, request_id: str, chunk: str) -> None:
        if not chunk:
            return

        with self._lock:
            job = self._jobs.get(request_id)
            if job is None:
                return

            execution = job.get("execution")
            if not isinstance(execution, dict):
                return

            current_output = execution.get("output", "")
            if not isinstance(current_output, str):
                current_output = ""
            execution["output"] = current_output + chunk

    def complete_job(
        self,
        request_id: str,
        *,
        success: bool,
        message: str,
        services: dict[str, dict[str, object]],
        finished_at: str,
    ) -> dict[str, object] | None:
        with self._lock:
            job = self._jobs.get(request_id)
            if job is None:
                return None

            job["status"] = "ok" if success else "error"
            job["message"] = message
            job["finished_at"] = finished_at
            job["services"] = deepcopy(services)

            if self._active_request_id == request_id:
                self._active_request_id = None

            return deepcopy(job)
