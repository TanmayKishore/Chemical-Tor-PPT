"""OpenAI LLM client with local disk response caching and retry handling."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..errors import LlmUnavailable

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"
FIXED_TEMPERATURE_PREFIXES = ("gpt-5", "gpt-6", "o1", "o3", "o4")
CONCURRENCY = 4
RATE_LIMIT_DELAY = 5.0
RETRY_DELAY = 2.0


def _env_number(name: str, default: float) -> float:
    try:
        return float(os.getenv(name) or default)
    except ValueError:
        return default


class LLMDisabled(RuntimeError):
    """Raised when LLM is requested during offline / disabled runs."""


class LLMClient:
    def __init__(self, model: Optional[str] = None, cache_dir: Optional[str] = None,
                 enabled: bool = True, chat: Any = None):
        self.model = model or os.getenv("PRESENTATION_LLM_MODEL") or DEFAULT_MODEL
        cache = cache_dir if cache_dir is not None else os.getenv("PRESENTATION_LLM_CACHE_DIR")
        self.cache_dir = Path(cache) if cache else None
        self.enabled = enabled
        self._chat = chat
        self._semaphore: Optional[asyncio.Semaphore] = None
        self.timeout = _env_number("PRESENTATION_LLM_TIMEOUT", 90.0)
        self.retries = int(_env_number("PRESENTATION_LLM_RETRIES", 1))
        self.calls = 0
        self.cache_hits = 0

    def _client(self) -> Any:
        if self._chat is None:
            from langchain_openai import ChatOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise LLMDisabled("OPENAI_API_KEY is not set")
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "timeout": self.timeout,
                "api_key": api_key,
            }
            if not any(self.model.startswith(p) for p in FIXED_TEMPERATURE_PREFIXES):
                kwargs["temperature"] = 0.0
            self._chat = ChatOpenAI(**kwargs)
        return self._chat

    def _cache_path(self, prompt: str) -> Optional[Path]:
        if not self.cache_dir:
            return None
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(f"{self.model}:{prompt}".encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.json"

    async def complete(self, prompt: str) -> str:
        """Execute a text completion prompt with caching and retries."""
        if not self.enabled:
            raise LLMDisabled("LLM calls are disabled for this run (--no-llm)")

        cache_file = self._cache_path(prompt)
        if cache_file and cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                self.cache_hits += 1
                return cached["response"]
            except Exception:
                pass

        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(CONCURRENCY)

        last_error = None
        for attempt in range(self.retries + 1):
            try:
                async with self._semaphore:
                    client = self._client()
                    resp = await client.ainvoke(prompt)
                    text_resp = resp.content if hasattr(resp, "content") else str(resp)
                    self.calls += 1
                    if cache_file:
                        cache_file.write_text(json.dumps({"prompt": prompt, "response": text_resp}), encoding="utf-8")
                    return text_resp
            except LLMDisabled:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    await asyncio.sleep(RETRY_DELAY)
                    continue

        raise LlmUnavailable(f"LLM call failed after {self.retries + 1} attempts: {last_error}") from last_error

