"""Tests for audio.postprocess — validates guard rails, not ffmpeg itself."""
from __future__ import annotations

from pathlib import Path

import pytest

from auto_podcast_crs.audio.postprocess import concat_mp3


def test_concat_empty_list_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="empty"):
        concat_mp3([], tmp_path / "out.mp3")


def test_concat_missing_chunk_raises(tmp_path: Path):
    missing = tmp_path / "nope.mp3"
    with pytest.raises(FileNotFoundError):
        concat_mp3([missing], tmp_path / "out.mp3")
