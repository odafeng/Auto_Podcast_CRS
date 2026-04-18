"""End-to-end pipeline for AI-generated podcasts."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .config import Config
from .script_generator import PodcastScript, ScriptGenerator
from .tts_converter import TTSConverter
from .audio_processor import AudioProcessor

logger = logging.getLogger(__name__)


class PodcastPipeline:
    """Orchestrates the full pipeline: script → TTS → audio merge.

    Usage
    -----
    >>> pipeline = PodcastPipeline()
    >>> output = pipeline.run("The future of renewable energy")
    >>> print(output)  # Path to the generated MP3 file
    """

    def __init__(
        self,
        config: Config | None = None,
        script_generator: ScriptGenerator | None = None,
        tts_converter: TTSConverter | None = None,
        audio_processor: AudioProcessor | None = None,
    ) -> None:
        self._config = config or Config()
        self._script_generator = script_generator or ScriptGenerator(self._config)
        self._tts_converter = tts_converter or TTSConverter(self._config)
        self._audio_processor = audio_processor or AudioProcessor()

    def run(self, topic: str) -> Path:
        """Run the full pipeline for *topic* and return the path to the episode MP3.

        Parameters
        ----------
        topic:
            The subject of the podcast episode.

        Returns
        -------
        Path
            Path to the final merged MP3 file.
        """
        self._config.validate()
        logger.info("=== Starting podcast pipeline for topic: %s ===", topic)

        # Step 1: Generate script
        script = self._script_generator.generate(topic)
        logger.info("Script generated – '%s' (%d segments)", script.title, len(script.segments))

        # Step 2: Convert script to audio segments
        segment_dir = self._config.OUTPUT_DIR / "segments"
        segment_paths = self._tts_converter.convert_script(script, output_dir=segment_dir)
        logger.info("TTS complete – %d audio segments", len(segment_paths))

        # Step 3: Merge segments into one episode file
        safe_title = _slugify(script.title)
        output_path = self._config.OUTPUT_DIR / f"{safe_title}.mp3"
        self._audio_processor.merge(segment_paths, output_path)

        logger.info("=== Pipeline complete → %s ===", output_path)
        return output_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Convert *text* to a safe filename slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:80]
