"""Audio processing module – merges segment files into a single podcast episode."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from pydub import AudioSegment

logger = logging.getLogger(__name__)

# Silence inserted between consecutive speaker turns (milliseconds)
_PAUSE_MS = 600

# Maps file extensions to pydub format strings
_EXT_FORMAT: dict[str, str] = {
    ".mp3": "mp3",
    ".wav": "wav",
    ".ogg": "ogg",
    ".flac": "flac",
}


class AudioProcessor:
    """Merges ordered audio segment files into one episode file.

    The output format is inferred from the file extension of *output_path*.
    Input segments are loaded with the format matching their own extension.
    """

    def __init__(self, pause_ms: int = _PAUSE_MS) -> None:
        self._pause_ms = pause_ms

    def merge(self, segment_paths: List[Path], output_path: Path) -> Path:
        """Concatenate *segment_paths* with short pauses and save to *output_path*.

        Parameters
        ----------
        segment_paths:
            Ordered list of paths to individual audio segment files.
        output_path:
            Destination file for the combined episode.  The file extension
            determines the output format (e.g. ``.mp3``, ``.wav``).

        Returns
        -------
        Path
            The path to the final combined audio file.

        Raises
        ------
        ValueError
            If *segment_paths* is empty.
        """
        if not segment_paths:
            raise ValueError("segment_paths must not be empty")

        pause = AudioSegment.silent(duration=self._pause_ms)
        combined = AudioSegment.empty()

        for idx, path in enumerate(segment_paths):
            logger.info("Merging segment %d: %s", idx, path)
            fmt = _EXT_FORMAT.get(path.suffix.lower(), "mp3")
            segment_audio = AudioSegment.from_file(str(path), format=fmt)
            if idx > 0:
                combined += pause
            combined += segment_audio

        output_fmt = _EXT_FORMAT.get(output_path.suffix.lower(), "mp3")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.export(str(output_path), format=output_fmt)
        logger.info("Episode saved to %s (duration %.1fs)", output_path, len(combined) / 1000)
        return output_path
