"""Tests for the retry wrapper. Stubs requests.post — no network."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from auto_podcast_crs._http import post_with_retry


def _fake_response(status: int, text: str = "", content: bytes = b""):
    """Build a minimal fake requests.Response."""
    m = MagicMock(spec=requests.Response)
    m.status_code = status
    m.reason = "TEST"
    m.text = text
    m.content = content

    def _raise():
        if status >= 400:
            err = requests.HTTPError(f"{status} error")
            err.response = m
            raise err

    m.raise_for_status.side_effect = _raise
    return m


def test_retries_on_500_then_succeeds():
    responses = [
        _fake_response(500),
        _fake_response(500),
        _fake_response(200, content=b"ok"),
    ]
    with patch("auto_podcast_crs._http.requests.post", side_effect=responses) as m:
        r = post_with_retry("https://example.com", timeout=5)
    assert r.status_code == 200
    assert m.call_count == 3


def test_retries_on_429():
    responses = [_fake_response(429), _fake_response(200, content=b"ok")]
    with patch("auto_podcast_crs._http.requests.post", side_effect=responses) as m:
        r = post_with_retry("https://example.com", timeout=5)
    assert r.status_code == 200
    assert m.call_count == 2


def test_does_not_retry_on_400():
    with patch(
        "auto_podcast_crs._http.requests.post",
        return_value=_fake_response(400, text="bad request"),
    ) as m:
        with pytest.raises(requests.HTTPError):
            post_with_retry("https://example.com", timeout=5)
    assert m.call_count == 1  # No retry on 4xx client errors


def test_gives_up_after_max_attempts():
    with patch(
        "auto_podcast_crs._http.requests.post",
        return_value=_fake_response(503),
    ) as m:
        with pytest.raises(requests.HTTPError):
            post_with_retry("https://example.com", timeout=5)
    # stop_after_attempt(4) → 4 total calls
    assert m.call_count == 4
