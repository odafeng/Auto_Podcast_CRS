"""Tests for src.tts_converter."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from src.script_generator import PodcastScript, ScriptSegment
from src.tts_converter import TTSConverter


def _make_config(output_dir: Path) -> MagicMock:
    from src.config import Config
    cfg = MagicMock(spec=Config)
    cfg.OPENAI_API_KEY = "sk-test"
    cfg.TTS_MODEL = "tts-1"
    cfg.HOST_VOICE = "alloy"
    cfg.GUEST_VOICE = "nova"
    cfg.OUTPUT_DIR = output_dir
    return cfg


def _make_converter(output_dir: Path) -> TTSConverter:
    cfg = _make_config(output_dir)
    converter = TTSConverter.__new__(TTSConverter)
    converter._config = cfg
    converter._voice_map = {"Host": "alloy", "Guest": "nova"}
    converter._client = MagicMock()
    return converter


def _make_script(n_turns: int = 3) -> PodcastScript:
    segments = []
    for i in range(n_turns):
        segments.append(ScriptSegment(
            speaker="Host" if i % 2 == 0 else "Guest",
            text=f"Text for turn {i}.",
        ))
    return PodcastScript(title="Test", description="desc", segments=segments)


class TestTTSConverter:
    def test_convert_segment_creates_file(self, tmp_path):
        converter = _make_converter(tmp_path)
        # Mock the API response so it writes to disk
        mock_response = MagicMock()
        mock_response.stream_to_file = MagicMock()
        converter._client.audio.speech.create.return_value = mock_response

        segment = ScriptSegment(speaker="Host", text="Hello world.")
        out = converter.convert_segment(segment, 0, tmp_path)

        assert out == tmp_path / "segment_000_host.mp3"
        mock_response.stream_to_file.assert_called_once_with(str(out))

    def test_convert_segment_uses_correct_voice_for_host(self, tmp_path):
        converter = _make_converter(tmp_path)
        mock_response = MagicMock()
        converter._client.audio.speech.create.return_value = mock_response

        segment = ScriptSegment(speaker="Host", text="Host says hi.")
        converter.convert_segment(segment, 0, tmp_path)

        create_call = converter._client.audio.speech.create.call_args
        assert create_call.kwargs["voice"] == "alloy"

    def test_convert_segment_uses_correct_voice_for_guest(self, tmp_path):
        converter = _make_converter(tmp_path)
        mock_response = MagicMock()
        converter._client.audio.speech.create.return_value = mock_response

        segment = ScriptSegment(speaker="Guest", text="Guest responds.")
        converter.convert_segment(segment, 1, tmp_path)

        create_call = converter._client.audio.speech.create.call_args
        assert create_call.kwargs["voice"] == "nova"

    def test_convert_script_returns_ordered_paths(self, tmp_path):
        converter = _make_converter(tmp_path)
        mock_response = MagicMock()
        converter._client.audio.speech.create.return_value = mock_response

        script = _make_script(n_turns=4)
        paths = converter.convert_script(script, output_dir=tmp_path / "segs")

        assert len(paths) == 4
        # Ensure they are ordered
        for i, path in enumerate(paths):
            assert f"segment_{i:03d}" in path.name

    def test_convert_script_creates_output_dir(self, tmp_path):
        converter = _make_converter(tmp_path)
        mock_response = MagicMock()
        converter._client.audio.speech.create.return_value = mock_response

        new_dir = tmp_path / "new_segments"
        assert not new_dir.exists()
        converter.convert_script(_make_script(1), output_dir=new_dir)
        assert new_dir.is_dir()

    def test_convert_script_default_output_dir(self, tmp_path):
        converter = _make_converter(tmp_path)
        mock_response = MagicMock()
        converter._client.audio.speech.create.return_value = mock_response

        # No output_dir supplied → should use config.OUTPUT_DIR / "segments"
        converter.convert_script(_make_script(1))
        expected_dir = tmp_path / "segments"
        assert expected_dir.is_dir()
