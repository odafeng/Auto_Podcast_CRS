"""v2 prompts must retain their conversational-style hallmarks.

This isn't a behavioral test (we can't grade script output without API calls).
It's a guardrail against future edits quietly deleting the key directives that
make v2 different from v1. If any of these fail, someone has probably started
editing v2 toward the lecture-mode style we moved away from.
"""
from __future__ import annotations

from pathlib import Path

import pytest

PROMPTS_DIR = (
    Path(__file__).resolve().parent.parent
    / "auto_podcast_crs" / "scripts" / "prompts"
)

V2_VERSIONS = ["v2_generic", "v2_persuasion", "v2_onboarding"]


@pytest.mark.parametrize("version", V2_VERSIONS)
def test_v2_prompt_forbids_listicle_structure(version):
    text = (PROMPTS_DIR / f"system_{version}.md").read_text(encoding="utf-8")
    # Every v2 prompt must explicitly forbid listicle structure, either by the
    # English term or by the "第一⋯第二⋯第三⋯" / "首先⋯其次⋯" CN equivalents.
    listicle_markers = ["listicle", "第一⋯第二⋯第三", "首先⋯其次⋯最後", "9 點順序"]
    assert any(m in text for m in listicle_markers), (
        f"{version} missing listicle prohibition"
    )


@pytest.mark.parametrize("version", V2_VERSIONS)
def test_v2_prompt_requires_filler_words(version):
    text = (PROMPTS_DIR / f"system_{version}.md").read_text(encoding="utf-8")
    # Must reference at least some of the filler-word bank
    fillers = ["欸", "然後呢", "對啊", "怎麼講"]
    hits = [f for f in fillers if f in text]
    assert len(hits) >= 3, (
        f"{version} references too few fillers ({hits}); must list concrete fillers"
    )


@pytest.mark.parametrize("version", V2_VERSIONS)
def test_v2_prompt_requires_direct_address(version):
    text = (PROMPTS_DIR / f"system_{version}.md").read_text(encoding="utf-8")
    # Must instruct the model to directly address the listener ("你")
    assert "你" in text
    # and must explicitly instruct direct listener addressing
    direct_markers = [
        "直接對", "對她說話", "對你說話", "對聽眾", "跟聽眾", "直接跟聽眾",
        "直接對她", "直接對聽眾",
    ]
    assert any(m in text for m in direct_markers), (
        f"{version} missing 'direct address' directive"
    )


@pytest.mark.parametrize("version", V2_VERSIONS)
def test_v2_prompt_bans_overacting_audio_tags(version):
    text = (PROMPTS_DIR / f"system_{version}.md").read_text(encoding="utf-8")
    # v2 must explicitly ban the overacting ElevenLabs tags
    for banned in ["[excited]", "[whispers]", "[shouts]"]:
        assert banned in text, f"{version} doesn't explicitly ban {banned}"
