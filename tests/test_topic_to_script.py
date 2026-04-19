"""Tests for TopicScriptAdapter — mocks Claude HTTP, verifies prompt construction."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from auto_podcast_crs.scripts.resources import load_resources
from auto_podcast_crs.scripts.topic_to_script import TopicScriptAdapter


def _fake_claude_response(script_text: str = "腳本內容 [CHUNK_BREAK] 第二段"):
    """Build a fake requests.Response returning a Claude-shaped JSON."""
    m = MagicMock()
    m.json.return_value = {
        "content": [{"type": "text", "text": script_text}],
        "usage": {"input_tokens": 1234, "output_tokens": 567},
    }
    m.status_code = 200
    m.raise_for_status.return_value = None
    return m


def _make_resources(tmp_path: Path, files: dict[str, str]) -> Path:
    d = tmp_path / "resources"
    d.mkdir()
    for name, content in files.items():
        (d / name).write_text(content)
    return d


def test_v3_prompt_loads():
    adapter = TopicScriptAdapter(prompt_version="v3_topic_generic")
    assert adapter.prompt_version == "v3_topic_generic"
    assert "腳本編輯" in adapter.system_prompt
    # The v3 prompt must reference resources/source handling
    assert "<source" in adapter.system_prompt or "resources" in adapter.system_prompt


def test_missing_prompt_raises():
    with pytest.raises(FileNotFoundError):
        TopicScriptAdapter(prompt_version="v99_does_not_exist")


def test_generate_calls_claude_with_topic_and_resources(tmp_path: Path):
    d = _make_resources(tmp_path, {"paper_a.md": "Finding: X improves Y by 10%."})
    bundle = load_resources(d)

    adapter = TopicScriptAdapter()
    with patch(
        "auto_podcast_crs.scripts.topic_to_script.post_with_retry",
        return_value=_fake_claude_response(),
    ) as mock_post:
        result = adapter.generate("機器人手術 learning curve", bundle)

    # Verify the HTTP call happened
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    body = kwargs["json"]

    # System prompt is the v3 one
    assert "腳本編輯" in body["system"]

    # User message includes topic + resources + instruction
    user_msg = body["messages"][0]["content"]
    assert "機器人手術 learning curve" in user_msg
    assert "<topic>" in user_msg
    assert "paper_a.md" in user_msg
    assert "X improves Y by 10%" in user_msg

    # Result fields populated
    assert result.resources_used == ["paper_a.md"]
    assert result.char_count > 0
    assert len(result.chunks) == 2  # split on [CHUNK_BREAK]
    assert result.metadata["topic"] == "機器人手術 learning curve"


def test_generate_includes_angle_when_provided(tmp_path: Path):
    d = _make_resources(tmp_path, {"a.md": "content"})
    bundle = load_resources(d)
    adapter = TopicScriptAdapter()
    with patch(
        "auto_podcast_crs.scripts.topic_to_script.post_with_retry",
        return_value=_fake_claude_response(),
    ) as mock_post:
        adapter.generate("主題 X", bundle, angle="trainee perspective")

    body = mock_post.call_args[1]["json"]
    user_msg = body["messages"][0]["content"]
    assert "<angle>" in user_msg
    assert "trainee perspective" in user_msg


def test_generate_rejects_empty_topic(tmp_path: Path):
    d = _make_resources(tmp_path, {"a.md": "content"})
    bundle = load_resources(d)
    adapter = TopicScriptAdapter()
    with pytest.raises(ValueError, match="topic must not be empty"):
        adapter.generate("   ", bundle)


def test_verbatim_copy_triggers_warning(tmp_path: Path, caplog):
    # Resource containing a distinctive long phrase, guaranteed > 40 chars
    phrase = (
        "這是一段非常具有辨識度的論文句子,剛好超過四十個字的長度用來測試,"
        "因為我們需要確保這個字串夠長可以觸發警告機制。"
    )
    assert len(phrase) >= 40
    d = _make_resources(tmp_path, {"paper.md": phrase})
    bundle = load_resources(d)

    # Model "cheats" by returning the phrase verbatim
    adapter = TopicScriptAdapter()
    with patch(
        "auto_podcast_crs.scripts.topic_to_script.post_with_retry",
        return_value=_fake_claude_response(f"開頭。{phrase}。結尾。"),
    ), caplog.at_level("WARNING"):
        adapter.generate("主題", bundle)

    messages = " ".join(r.message for r in caplog.records)
    assert "verbatim" in messages.lower()
