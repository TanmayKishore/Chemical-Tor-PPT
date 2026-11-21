"""In-memory jobs worker for asynchronous presentation requests."""

from __future__ import annotations

import asyncio
import contextvars
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict

from fastapi import APIRouter, HTTPException

from ..errors import BadRequest, LlmUnavailable, SectionFailed, SourcesUnavailable, StorageError

logger = logging.getLogger("jobs")
KEEP_SECONDS = 2 * 3600

run_context = contextvars.ContextVar("run_context", default="")


class RunContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.run = run_context.get() or "service"
        return True


router = APIRouter(prefix="/jobs", tags=["jobs"])
_JOBS: Dict[str, Dict[str, Any]] = {}


def running() -> int:
    return sum(1 for job in _JOBS.values() if job["status"] in ("pending", "running"))


def _clean_old_jobs() -> None:
    now = time.time()
    expired = [jid for jid, j in _JOBS.items() if j["status"] in ("completed", "failed") and now - j.get("finished_at", 0) > KEEP_SECONDS]
    for jid in expired:
        _JOBS.pop(jid, None)


async def start_job(work: Callable[[str], Awaitable[Dict[str, Any]]], project_id: str) -> str:
    _clean_old_jobs()
    job_id = str(uuid.uuid4())
    _JOBS[job_id] = {
        "job_id": job_id,
        "project_id": project_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }

    async def runner():
        _JOBS[job_id]["status"] = "running"
        try:
            res = await work(project_id)
            _JOBS[job_id]["status"] = "completed"
            _JOBS[job_id]["result"] = res
        except Exception as exc:
            logger.error("[Jobs] Job %s failed: %s", job_id, exc, exc_info=True)
            _JOBS[job_id]["status"] = "failed"
            _JOBS[job_id]["error"] = str(exc)
        finally:
            _JOBS[job_id]["finished_at"] = time.time()

    asyncio.create_task(runner())
    return job_id


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

