"""CLI: run TTS on a generated script.

Usage:
    python scripts/run_tts.py --episode 04_xxx
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auto_podcast_crs._logging import setup_logging  # noqa: E402
from auto_podcast_crs.audio import concat_mp3, get_audio_duration  # noqa: E402
from auto_podcast_crs.scripts.claude_monologue import split_chunks  # noqa: E402
from auto_podcast_crs.tts.elevenlabs_v3 import ElevenLabsV3TTS  # noqa: E402

log = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True, help="Episode folder name")
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()

    setup_logging(args.log_level)

    repo_root = Path(__file__).resolve().parent.parent
    episode_dir = repo_root / "episodes" / args.episode
    script_path = episode_dir / "script.txt"

    if not script_path.exists():
        log.error("Script not found: %s. Run generate_script.py first.", script_path)
        return 1

    script_text = script_path.read_text(encoding="utf-8").strip()
    chunks = split_chunks(script_text)

    if not chunks:
        log.error("Script produced zero chunks after splitting on [CHUNK_BREAK].")
        return 1

    log.info("Episode: %s", args.episode)
    log.info("Chunks:  %d", len(chunks))
    for i, c in enumerate(chunks):
        log.info("  chunk %d: %d chars", i, len(c))

    work_dir = episode_dir / "tts_chunks"
    output_path = episode_dir / f"{args.episode}_full.mp3"

    tts = ElevenLabsV3TTS()
    result = tts.synthesize(chunks, output_dir=work_dir)

    concat_mp3(result.chunk_paths, output_path)
    duration = get_audio_duration(output_path)
    size_mb = output_path.stat().st_size / (1024 * 1024)

    log.info("=== Done ===")
    log.info("Output:   %s", output_path)
    log.info("Duration: %.1fs (%.1f min)", duration, duration / 60)
    log.info("Size:     %.2f MB", size_mb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
