"""Tests for src.pipeline (PodcastPipeline orchestrator)."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from src.pipeline import PodcastPipeline, _slugify
from src.script_generator import PodcastScript, ScriptSegment


def _make_mock_script(n_turns: int = 4) -> PodcastScript:
    segments = [
        ScriptSegment(speaker="Host" if i % 2 == 0 else "Guest", text=f"Turn {i}.")
        for i in range(n_turns)
    ]
    return PodcastScript(title="AI and the Future", description="Episode about AI", segments=segments)


class TestSlugify:
    def test_basic(self):
        assert _slugify("Hello World") == "hello_world"

    def test_special_chars_removed(self):
        assert _slugify("AI & the Future!") == "ai_the_future"

    def test_long_title_truncated(self):
        long = "a" * 100
        assert len(_slugify(long)) <= 80

    def test_spaces_become_underscores(self):
        assert _slugify("foo bar baz") == "foo_bar_baz"

    def test_hyphens_normalised(self):
        result = _slugify("foo-bar--baz")
        assert result == "foo_bar_baz"


class TestPodcastPipeline:
    def _make_pipeline(self, tmp_path: Path) -> tuple[PodcastPipeline, MagicMock, MagicMock, MagicMock]:
        from src.config import Config
        cfg = MagicMock(spec=Config)
        cfg.OPENAI_API_KEY = "sk-test"
        cfg.OUTPUT_DIR = tmp_path
        cfg.validate = MagicMock()

        mock_gen = MagicMock()
        mock_tts = MagicMock()
        mock_audio = MagicMock()

        pipeline = PodcastPipeline(
            config=cfg,
            script_generator=mock_gen,
            tts_converter=mock_tts,
            audio_processor=mock_audio,
        )
        return pipeline, mock_gen, mock_tts, mock_audio

    def test_run_calls_validate(self, tmp_path):
        pipeline, mock_gen, mock_tts, mock_audio = self._make_pipeline(tmp_path)
        script = _make_mock_script()
        mock_gen.generate.return_value = script
        mock_tts.convert_script.return_value = [tmp_path / "seg.mp3"]
        mock_audio.merge.return_value = tmp_path / "episode.mp3"

        pipeline.run("AI")
        pipeline._config.validate.assert_called_once()

    def test_run_calls_script_generator_with_topic(self, tmp_path):
        pipeline, mock_gen, mock_tts, mock_audio = self._make_pipeline(tmp_path)
        script = _make_mock_script()
        mock_gen.generate.return_value = script
        mock_tts.convert_script.return_value = [tmp_path / "seg.mp3"]
        mock_audio.merge.return_value = tmp_path / "episode.mp3"

        pipeline.run("Renewable Energy")
        mock_gen.generate.assert_called_once_with("Renewable Energy")

    def test_run_calls_tts_with_script(self, tmp_path):
        pipeline, mock_gen, mock_tts, mock_audio = self._make_pipeline(tmp_path)
        script = _make_mock_script()
        mock_gen.generate.return_value = script
        mock_tts.convert_script.return_value = [tmp_path / "seg.mp3"]
        mock_audio.merge.return_value = tmp_path / "episode.mp3"

        pipeline.run("Topic")
        mock_tts.convert_script.assert_called_once()
        call_args = mock_tts.convert_script.call_args
        assert call_args.args[0] is script or call_args.kwargs.get("script") is script

    def test_run_calls_audio_merge(self, tmp_path):
        pipeline, mock_gen, mock_tts, mock_audio = self._make_pipeline(tmp_path)
        script = _make_mock_script()
        fake_segments = [tmp_path / f"seg_{i}.mp3" for i in range(4)]
        mock_gen.generate.return_value = script
        mock_tts.convert_script.return_value = fake_segments
        expected_out = tmp_path / "episode.mp3"
        mock_audio.merge.return_value = expected_out

        pipeline.run("Topic")
        mock_audio.merge.assert_called_once()
        merge_args = mock_audio.merge.call_args
        assert merge_args.args[0] == fake_segments or merge_args.kwargs.get("segment_paths") == fake_segments

    def test_run_returns_output_path(self, tmp_path):
        pipeline, mock_gen, mock_tts, mock_audio = self._make_pipeline(tmp_path)
        script = _make_mock_script()
        mock_gen.generate.return_value = script
        mock_tts.convert_script.return_value = [tmp_path / "seg.mp3"]
        expected = tmp_path / "ai_and_the_future.mp3"
        mock_audio.merge.return_value = expected

        result = pipeline.run("AI")
        assert result == expected

    def test_run_output_filename_derived_from_title(self, tmp_path):
        pipeline, mock_gen, mock_tts, mock_audio = self._make_pipeline(tmp_path)
        script = PodcastScript(
            title="Space Exploration", description="", segments=[ScriptSegment("Host", "Hi.")]
        )
        mock_gen.generate.return_value = script
        mock_tts.convert_script.return_value = [tmp_path / "seg.mp3"]
        mock_audio.merge.return_value = tmp_path / "space_exploration.mp3"

        pipeline.run("space exploration")
        merge_call = mock_audio.merge.call_args
        output_path = merge_call.args[1] if len(merge_call.args) > 1 else merge_call.kwargs["output_path"]
        assert "space_exploration" in output_path.name
