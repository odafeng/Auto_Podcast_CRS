"""Text-to-speech conversion module – converts script segments to audio files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from openai import OpenAI

from .config import Config
from .script_generator import PodcastScript, ScriptSegment

logger = logging.getLogger(__name__)

# Maps speaker role → voice name
_DEFAULT_VOICE_MAP = {
    "Host": "alloy",
    "Guest": "nova",
}


class TTSConverter:
    """Converts each :class:`ScriptSegment` into an MP3 audio file via OpenAI TTS."""

    def __init__(self, config: Config | None = None) -> None:
        self._config = config or Config()
        self._client = OpenAI(api_key=self._config.OPENAI_API_KEY)
        self._voice_map = {
            "Host": self._config.HOST_VOICE,
            "Guest": self._config.GUEST_VOICE,
        }

    def convert_script(self, script: PodcastScript, output_dir: Path | None = None) -> List[Path]:
        """Convert every segment of *script* to an MP3 file.

        Parameters
        ----------
        script:
            The podcast script produced by :class:`ScriptGenerator`.
        output_dir:
            Directory where segment files are saved.  Defaults to
            ``Config.OUTPUT_DIR / "segments"``.

        Returns
        -------
        List[Path]
            Ordered list of paths to the generated MP3 segment files.
        """
        if output_dir is None:
            output_dir = self._config.OUTPUT_DIR / "segments"
        output_dir.mkdir(parents=True, exist_ok=True)

        paths: List[Path] = []
        for idx, segment in enumerate(script.segments):
            path = self.convert_segment(segment, idx, output_dir)
            paths.append(path)
        return paths

    def convert_segment(
        self,
        segment: ScriptSegment,
        index: int,
        output_dir: Path,
    ) -> Path:
        """Convert a single *segment* to an MP3 file.

        Parameters
        ----------
        segment:
            A single spoken turn.
        index:
            Zero-based position in the script (used for file naming).
        output_dir:
            Directory to save the file in.

        Returns
        -------
        Path
            Path to the saved MP3 file.
        """
        voice = self._voice_map.get(segment.speaker, self._config.HOST_VOICE)
        filename = output_dir / f"segment_{index:03d}_{segment.speaker.lower()}.mp3"

        logger.info(
            "TTS segment %d (%s, voice=%s): %s...",
            index,
            segment.speaker,
            voice,
            segment.text[:60],
        )

        response = self._client.audio.speech.create(
            model=self._config.TTS_MODEL,
            voice=voice,  # type: ignore[arg-type]
            input=segment.text,
        )
        response.stream_to_file(str(filename))
        logger.debug("Saved segment to %s", filename)
        return filename
