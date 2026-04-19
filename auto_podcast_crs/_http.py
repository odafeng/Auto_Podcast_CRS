"""Shared HTTP helper with exponential-backoff retry.

Retries on 5xx, 429, and network errors. Does NOT retry on 4xx (other than 429) —
those are request-side bugs we want surfaced fast, not papered over.
"""
from __future__ import annotations

import logging
from typing import Any

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class RetryableHTTPError(requests.HTTPError):
    """HTTP error that should trigger a retry."""


def _raise_retryable(resp: requests.Response) -> None:
    """Raise RetryableHTTPError on 5xx/429. Otherwise call raise_for_status()."""
    if resp.status_code in RETRYABLE_STATUS:
        raise RetryableHTTPError(
            f"{resp.status_code} {resp.reason}: {resp.text[:200]}",
            response=resp,
        )
    resp.raise_for_status()


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type(
        (requests.ConnectionError, requests.Timeout, RetryableHTTPError)
    ),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def post_with_retry(url: str, *, timeout: int = 120, **kwargs: Any) -> requests.Response:
    """POST with retry on 5xx/429/connection errors. 4xx raises immediately."""
    resp = requests.post(url, timeout=timeout, **kwargs)
    _raise_retryable(resp)
    return resp
