"""Service settings, read from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_DB_URL = "https://eiacommonfastapi-production.up.railway.app"
DB_BASE_URL = (os.getenv("DB_API_BASE_URL") or os.getenv("DB_BASE_URL") or DEFAULT_DB_URL).rstrip("/")


def _number(name: str, default: float) -> float:
    try:
        return float(os.getenv(name) or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class JobSettings:
    """Settings controlling concurrency and job deadlines."""
    max_jobs: int = 2
    deadline_s: float = 25 * 60

    @classmethod
    def from_env(cls) -> "JobSettings":
        return cls(max_jobs=max(1, int(_number("PRESENTATION_MAX_JOBS", cls.max_jobs))),
                   deadline_s=_number("PRESENTATION_JOB_DEADLINE", cls.deadline_s))

