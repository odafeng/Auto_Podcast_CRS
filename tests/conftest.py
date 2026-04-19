"""Shared pytest fixtures."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _stub_env(monkeypatch):
    """Ensure tests never hit real APIs or leak credentials."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-for-tests")
    monkeypatch.setenv("ELEVEN_API_KEY", "fake-eleven-key")
    monkeypatch.setenv("ELEVEN_VOICE_ID", "fake-voice-id")
    # Force settings cache reload so the stubs take effect
    from auto_podcast_crs import config
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()
