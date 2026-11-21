"""Presentation routes: POST /jobs and ONLYOFFICE proxy."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .jobs import running, start_job
from ..generate import DeckRequest, generate
from ..settings import JobSettings

logger = logging.getLogger(__name__)
router = APIRouter()


class JobRequest(BaseModel):
    project_id: str
    presentation_type: str = "chemical_tor"
    presentation_category: str = "B1"
    presentation_date: Optional[str] = None
    statutory: Dict[str, Any] = Field(default_factory=dict)
    common_details: Dict[str, Any] = Field(default_factory=dict)


@router.post("/jobs")
async def create_presentation_job(payload: JobRequest, request: Request):
    settings = JobSettings.from_env()
    if running() >= settings.max_jobs:
        raise HTTPException(status_code=503, detail="Instance is busy processing maximum concurrent jobs")

    async def work(project_id: str):
        deck_req = DeckRequest(
            project_id=project_id,
            presentation_type=payload.presentation_type,
            presentation_category=payload.presentation_category,
            presentation_date=payload.presentation_date,
            statutory=payload.statutory,
            common_details=payload.common_details,
        )
        filename, pptx_bytes, metadata = await generate(deck_req)
        return metadata

    job_id = await start_job(work, payload.project_id)
    return {"job_id": job_id, "status": "pending"}

