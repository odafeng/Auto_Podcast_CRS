"""Tests for src.audio_processor."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from src.audio_processor import AudioProcessor


def _write_fake_wav(path: Path) -> Path:
    """Write a minimal silent WAV file (no ffmpeg required)."""
    from pydub import AudioSegment
    audio = AudioSegment.silent(duration=200)
    audio.export(str(path), format="wav")
    return path


class TestAudioProcessor:
    def test_merge_raises_on_empty_list(self):
        processor = AudioProcessor()
        with pytest.raises(ValueError, match="empty"):
            processor.merge([], Path("/tmp/out.wav"))

    def test_merge_single_segment(self, tmp_path):
        seg = _write_fake_wav(tmp_path / "seg_000.wav")
        out = tmp_path / "episode.wav"
        processor = AudioProcessor(pause_ms=100)
        result = processor.merge([seg], out)
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_merge_multiple_segments(self, tmp_path):
        segs = [_write_fake_wav(tmp_path / f"seg_{i:03d}.wav") for i in range(3)]
        out = tmp_path / "episode.wav"
        processor = AudioProcessor(pause_ms=100)
        result = processor.merge(segs, out)
        assert result == out
        assert out.exists()

    def test_merge_output_longer_than_single_segment(self, tmp_path):
        """Combined file should be longer than any single 200 ms segment."""
        from pydub import AudioSegment
        segs = [_write_fake_wav(tmp_path / f"seg_{i:03d}.wav") for i in range(3)]
        out = tmp_path / "episode.wav"
        processor = AudioProcessor(pause_ms=0)
        processor.merge(segs, out)
        combined = AudioSegment.from_file(str(out), format="wav")
        # 3 segments × 200 ms each = 600 ms (allow 10 ms tolerance)
        assert len(combined) >= 590

    def test_merge_creates_parent_dir(self, tmp_path):
        seg = _write_fake_wav(tmp_path / "seg.wav")
        nested_out = tmp_path / "nested" / "deep" / "episode.wav"
        processor = AudioProcessor()
        processor.merge([seg], nested_out)
        assert nested_out.exists()

    def test_custom_pause_applied(self, tmp_path):
        """Verify that a longer pause results in a longer output file."""
        from pydub import AudioSegment
        segs = [_write_fake_wav(tmp_path / f"seg_{i}.wav") for i in range(2)]

        out_no_pause = tmp_path / "no_pause.wav"
        out_long_pause = tmp_path / "long_pause.wav"

        AudioProcessor(pause_ms=0).merge(segs, out_no_pause)
        AudioProcessor(pause_ms=500).merge(segs, out_long_pause)

        dur_no_pause = len(AudioSegment.from_file(str(out_no_pause), format="wav"))
        dur_long_pause = len(AudioSegment.from_file(str(out_long_pause), format="wav"))
        assert dur_long_pause > dur_no_pause
