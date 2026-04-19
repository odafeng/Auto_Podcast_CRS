"""Tests for audio.postprocess — validates guard rails, not ffmpeg itself.

These tests MUST pass even when ffmpeg is not installed. Input validation
should fail fast before any external-binary check, so caller bugs surface
as ValueError / FileNotFoundError rather than RuntimeError('ffmpeg not in PATH').
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from auto_podcast_crs.audio.postprocess import concat_mp3


def test_concat_empty_list_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="empty"):
        concat_mp3([], tmp_path / "out.mp3")


def test_concat_missing_chunk_raises(tmp_path: Path):
    missing = tmp_path / "nope.mp3"
    with pytest.raises(FileNotFoundError):
        concat_mp3([missing], tmp_path / "out.mp3")


def test_input_validation_runs_before_ffmpeg_check(tmp_path: Path):
    """Regression test: if ffmpeg check runs first, bad inputs get masked as
    'ffmpeg not in PATH' instead of the true ValueError/FileNotFoundError.
    This test simulates a missing ffmpeg and confirms input errors still
    surface correctly."""
    with patch("auto_podcast_crs.audio.postprocess.shutil.which", return_value=None):
        # Empty list: should raise ValueError, NOT RuntimeError about ffmpeg
        with pytest.raises(ValueError, match="empty"):
            concat_mp3([], tmp_path / "out.mp3")
        # Missing chunk: should raise FileNotFoundError, NOT RuntimeError
        with pytest.raises(FileNotFoundError):
            concat_mp3([tmp_path / "nope.mp3"], tmp_path / "out.mp3")
