"""Audio post-processing helpers built on ffmpeg."""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


def _require(binary: str) -> None:
    if shutil.which(binary) is None:
        raise RuntimeError(f"{binary} not found in PATH")


def concat_mp3(chunk_paths: list[Path], output_path: Path) -> None:
    """Concat MP3 chunks without re-encoding (lossless, fast)."""
    # Validate inputs first — these are caller bugs and should fail fast,
    # independent of whether ffmpeg is installed.
    if not chunk_paths:
        raise ValueError("concat_mp3 called with empty chunk_paths")
    for p in chunk_paths:
        if not p.exists():
            raise FileNotFoundError(f"Chunk not found: {p}")

    # Only after inputs check out, require ffmpeg.
    _require("ffmpeg")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_list = output_path.parent / f".concat_{output_path.stem}.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in chunk_paths),
        encoding="utf-8",
    )
    try:
        log.info("Concatenating %d chunks → %s", len(chunk_paths), output_path)
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed:\n{result.stderr}")
    finally:
        concat_list.unlink(missing_ok=True)


def get_audio_duration(path: Path) -> float:
    """Return duration in seconds via ffprobe."""
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    _require("ffprobe")
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return float(result.stdout.strip())
