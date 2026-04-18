"""Tests for src.script_generator."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.script_generator import PodcastScript, ScriptGenerator, ScriptSegment


def _make_raw_json(title="Test Title", description="Test desc", n_turns=4) -> str:
    segments = []
    for i in range(n_turns):
        speaker = "Host" if i % 2 == 0 else "Guest"
        segments.append({"speaker": speaker, "text": f"This is turn {i}."})
    return json.dumps({"title": title, "description": description, "segments": segments})


class TestScriptGeneratorParse:
    """Unit tests for the static _parse method (no API calls)."""

    def test_parse_returns_podcast_script(self):
        raw = _make_raw_json()
        script = ScriptGenerator._parse(raw)
        assert isinstance(script, PodcastScript)

    def test_parse_title_and_description(self):
        raw = _make_raw_json(title="My Episode", description="About things")
        script = ScriptGenerator._parse(raw)
        assert script.title == "My Episode"
        assert script.description == "About things"

    def test_parse_segments_count(self):
        raw = _make_raw_json(n_turns=6)
        script = ScriptGenerator._parse(raw)
        assert len(script.segments) == 6

    def test_parse_segments_type(self):
        raw = _make_raw_json(n_turns=2)
        script = ScriptGenerator._parse(raw)
        for seg in script.segments:
            assert isinstance(seg, ScriptSegment)
            assert seg.speaker in ("Host", "Guest")
            assert isinstance(seg.text, str)

    def test_parse_invalid_json_raises_value_error(self):
        with pytest.raises(ValueError, match="invalid JSON"):
            ScriptGenerator._parse("not-json{{{")

    def test_parse_empty_segments(self):
        raw = json.dumps({"title": "Empty", "description": "", "segments": []})
        script = ScriptGenerator._parse(raw)
        assert script.segments == []

    def test_parse_missing_title_uses_default(self):
        raw = json.dumps({"description": "no title", "segments": []})
        script = ScriptGenerator._parse(raw)
        assert script.title == "Untitled Episode"


class TestScriptGeneratorGenerate:
    """Integration-style tests with the OpenAI client mocked."""

    def _make_generator(self) -> ScriptGenerator:
        from src.config import Config
        cfg = MagicMock(spec=Config)
        cfg.OPENAI_API_KEY = "sk-test"
        cfg.SCRIPT_MODEL = "gpt-4o"
        gen = ScriptGenerator.__new__(ScriptGenerator)
        gen._config = cfg
        gen._client = MagicMock()
        return gen

    def test_generate_calls_chat_completions(self):
        gen = self._make_generator()
        raw = _make_raw_json(title="AI Future", n_turns=4)
        gen._client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=raw))]
        )
        script = gen.generate("AI Future")
        assert script.title == "AI Future"
        gen._client.chat.completions.create.assert_called_once()

    def test_generate_passes_topic_in_user_message(self):
        gen = self._make_generator()
        raw = _make_raw_json()
        gen._client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=raw))]
        )
        gen.generate("Quantum Computing")
        call_kwargs = gen._client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs.args[0]
        if isinstance(messages, dict):
            messages = call_kwargs.kwargs["messages"]
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "Quantum Computing" in user_msg["content"]
