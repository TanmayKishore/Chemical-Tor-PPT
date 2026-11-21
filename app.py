"""FastAPI Application entry point for Chemical ToR presentation agent."""

import logging
import os
from dotenv import load_dotenv

_local_env = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_local_env):
    load_dotenv(_local_env)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.api.jobs import RunContextFilter, router as jobs_router
from agent.api.presentation import router as presentation_router

SERVICE = "chemical-tor-presentation-agent"


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RunContextFilter())
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s [%(run)s] %(message)s"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


configure_logging()

app = FastAPI(title="Chemical ToR Presentation Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(presentation_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": SERVICE}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)

