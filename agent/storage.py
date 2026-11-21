"""Uploads finished presentations to object storage and registers the document."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from .errors import StorageError
from .settings import DB_BASE_URL

logger = logging.getLogger(__name__)

BASE_URL = DB_BASE_URL
PPTX_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


async def upload(project_id: str, pptx_bytes: bytes, presentation_type: str = "chemical_tor",
                 client: Optional[httpx.AsyncClient] = None) -> str:
    """Store the .pptx in storage bucket and return its retrieval URL."""
    bucket_path = f"{project_id}/{presentation_type}_presentation.pptx"
    url = f"{BASE_URL}/db/bucket/upload"
    files = {"file": (f"{presentation_type}_presentation.pptx", pptx_bytes, PPTX_TYPE)}
    data = {"path": bucket_path}

    try:
        if client is not None:
            response = await client.post(url, files=files, data=data)
        else:
            async with httpx.AsyncClient(timeout=120.0) as local_client:
                response = await local_client.post(url, files=files, data=data)
    except Exception as exc:
        logger.error("[Storage] Upload failed for %s: %s", bucket_path, exc)
        raise StorageError(f"Upload to storage failed: {exc}") from exc

    if response.status_code not in (200, 201):
        raise StorageError(f"Upload to storage failed with status {response.status_code}: {response.text}")

    return f"{BASE_URL}/db/bucket/get_from_bucket/{bucket_path}"


async def register(project_id: str, doc_url: str, presentation_type: str = "chemical_tor",
                   client: Optional[httpx.AsyncClient] = None) -> None:
    """Record the document in generated_documents table."""
    url = f"{BASE_URL}/db/create_generated_document"
    payload = {
        "project_id": project_id,
        "document_type": "presentation",
        "document_subtype": presentation_type,
        "version": 1,
        "document_url": doc_url,
    }
    try:
        if client is not None:
            response = await client.post(url, json=payload)
        else:
            async with httpx.AsyncClient(timeout=30.0) as local_client:
                response = await local_client.post(url, json=payload)
    except Exception as exc:
        logger.error("[Storage] Registration failed for %s: %s", project_id, exc)
        raise StorageError(f"Document registration failed: {exc}") from exc

    if response.status_code not in (200, 201):
        raise StorageError(f"Document registration failed with status {response.status_code}: {response.text}")


async def store_deck(project_id: str, pptx_bytes: bytes, presentation_type: str = "chemical_tor",
                     client: Optional[httpx.AsyncClient] = None) -> str:
    """Upload and register finished deck."""
    url = await upload(project_id, pptx_bytes, presentation_type, client=client)
    await register(project_id, url, presentation_type, client=client)
    return url

