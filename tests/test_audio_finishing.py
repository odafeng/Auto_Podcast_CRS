"""Tests for audio.finishing — guard rails + real ffmpeg smoke tests.

The smoke tests generate silent MP3s via ffmpeg (cheap, ~1s each) to verify
the finishing functions actually work end-to-end on real audio files.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from auto_podcast_crs.audio.finishing import (
    finish_episode,
    normalize_lufs,
    splice_intro_outro,
)

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not available",
)


def _silent_mp3(path: Path, seconds: float = 0.5) -> None:
    """Generate a short MP3 for testing.

    Not actually silent — loudnorm asserts on silent input (ffmpeg bug
    https://trac.ffmpeg.org/ticket/7387). We emit a low-amplitude sine
    tone instead.
    """
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=440:sample_rate=44100",
            "-t", str(seconds),
            "-af", "volume=0.05",
            "-b:a", "128k",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def test_splice_no_intro_outro_copies_main(tmp_path: Path):
    main = tmp_path / "main.mp3"
    out = tmp_path / "out.mp3"
    _silent_mp3(main, 0.3)

    splice_intro_outro(main, out, intro_path=None, outro_path=None)

    assert out.exists()
    # Should be a straight copy
    assert out.read_bytes() == main.read_bytes()


def test_splice_with_intro_and_outro(tmp_path: Path):
    intro = tmp_path / "intro.mp3"
    main = tmp_path / "main.mp3"
    outro = tmp_path / "outro.mp3"
    out = tmp_path / "out.mp3"
    _silent_mp3(intro, 0.2)
    _silent_mp3(main, 0.5)
    _silent_mp3(outro, 0.2)

    splice_intro_outro(main, out, intro_path=intro, outro_path=outro)

    assert out.exists()
    # Spliced file should be larger than main alone
    assert out.stat().st_size > main.stat().st_size


def test_splice_missing_main_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Main audio"):
        splice_intro_outro(
            tmp_path / "missing.mp3",
            tmp_path / "out.mp3",
        )


def test_splice_missing_intro_raises(tmp_path: Path):
    main = tmp_path / "main.mp3"
    _silent_mp3(main, 0.3)
    with pytest.raises(FileNotFoundError, match="intro audio"):
        splice_intro_outro(
            main,
            tmp_path / "out.mp3",
            intro_path=tmp_path / "missing_intro.mp3",
        )


def test_normalize_lufs_produces_output(tmp_path: Path):
    src = tmp_path / "src.mp3"
    out = tmp_path / "out.mp3"
    _silent_mp3(src, 1.0)

    normalize_lufs(src, out, target_lufs=-16.0)

    assert out.exists()
    assert out.stat().st_size > 0


def test_normalize_lufs_missing_input_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        normalize_lufs(tmp_path / "nope.mp3", tmp_path / "out.mp3")


def test_finish_episode_no_intro_outro(tmp_path: Path):
    main = tmp_path / "main.mp3"
    out = tmp_path / "final.mp3"
    _silent_mp3(main, 1.0)

    finish_episode(main, out)

    assert out.exists()
    # Temp splice file should be cleaned up
    tmp_splice = out.parent / f".splice_tmp_{out.stem}.mp3"
    assert not tmp_splice.exists()


def test_finish_episode_full_pipeline(tmp_path: Path):
    intro = tmp_path / "intro.mp3"
    main = tmp_path / "main.mp3"
    outro = tmp_path / "outro.mp3"
    final = tmp_path / "final.mp3"
    _silent_mp3(intro, 0.3)
    _silent_mp3(main, 1.0)
    _silent_mp3(outro, 0.3)

    finish_episode(main, final, intro_path=intro, outro_path=outro)

    assert final.exists()
