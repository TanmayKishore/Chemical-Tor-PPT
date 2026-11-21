"""Errors raised by the Chemical ToR presentation agent."""

from __future__ import annotations


class BadRequest(ValueError):
    """The request names a deck or parameters that cannot be built for this project."""


class SourcesUnavailable(RuntimeError):
    """Upstream data source could not be reached or returned 5xx for required records."""


class LlmUnavailable(RuntimeError):
    """The model did not answer after configured retries."""


class StorageError(RuntimeError):
    """The finished presentation could not be saved to storage."""


class SectionFailed(RuntimeError):
    """One section of the deck failed execution; the deck is incomplete."""

    def __init__(self, section_id: str, cause: BaseException):
        self.section_id = section_id
        self.cause = cause
        super().__init__(f"section {section_id}: {type(cause).__name__}: {cause}")

