"""Tests for prompt loading — catches missing prompt files before network calls."""
from __future__ import annotations

import pytest

from auto_podcast_crs.scripts.claude_monologue import ClaudeScriptAdapter


def test_bundled_prompt_loads():
    adapter = ClaudeScriptAdapter(prompt_version="v1_generic")
    assert len(adapter.system_prompt) > 100


def test_missing_prompt_raises():
    with pytest.raises(FileNotFoundError):
        ClaudeScriptAdapter(prompt_version="v99_does_not_exist")


@pytest.mark.parametrize(
    "version", ["v1_generic", "v1_persuasion", "v1_onboarding"]
)
def test_all_shipped_prompts_load(version):
    adapter = ClaudeScriptAdapter(prompt_version=version)
    assert adapter.prompt_version == version
    assert adapter.system_prompt


def test_model_override():
    adapter = ClaudeScriptAdapter(prompt_version="v1_generic", model="custom-model-id")
    assert adapter.model == "custom-model-id"


def test_max_tokens_override():
    adapter = ClaudeScriptAdapter(prompt_version="v1_generic", max_tokens=1234)
    assert adapter.max_tokens == 1234
