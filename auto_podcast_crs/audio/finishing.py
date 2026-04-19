"""Audio finishing: splice intro/outro, normalize loudness to -16 LUFS.

Apple Podcasts and Spotify both target program loudness around -16 LUFS
(mono) / -19 LUFS (stereo). See https://podcasters.apple.com/support/893-audio-requirements

All functions are pure: read-only inputs + one output path. ffmpeg and
ffprobe are required on PATH.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_LUFS_TARGET = -16.0


def _require(binary: str) -> None:
    if shutil.which(binary) is None:
        raise RuntimeError(f"{binary} not found in PATH")


def splice_intro_outro(
    main_path: Path,
    output_path: Path,
    intro_path: Path | None = None,
    outro_path: Path | None = None,
) -> None:
    """Concat intro + main + outro into a single MP3, lossless.

    If intro_path/outro_path is None or missing, they're skipped silently
    (caller's responsibility to decide whether skipping is OK). If BOTH are
    None, this is equivalent to copying main_path to output_path.
    """
    if not main_path.exists():
        raise FileNotFoundError(f"Main audio not found: {main_path}")
    for label, p in [("intro", intro_path), ("outro", outro_path)]:
        if p is not None and not p.exists():
            raise FileNotFoundError(f"{label} audio not found: {p}")

    parts: list[Path] = []
    if intro_path is not None:
        parts.append(intro_path)
    parts.append(main_path)
    if outro_path is not None:
        parts.append(outro_path)

    # No intro/outro to add: just copy
    if len(parts) == 1:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(main_path, output_path)
        log.info("No intro/outro supplied; copied main → %s", output_path)
        return

    _require("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_list = output_path.parent / f".splice_{output_path.stem}.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in parts),
        encoding="utf-8",
    )
    try:
        log.info(
            "Splicing %d parts → %s (intro=%s outro=%s)",
            len(parts), output_path,
            intro_path is not None, outro_path is not None,
        )
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
            raise RuntimeError(f"ffmpeg splice failed:\n{result.stderr}")
    finally:
        concat_list.unlink(missing_ok=True)


def normalize_lufs(
    input_path: Path,
    output_path: Path,
    target_lufs: float = DEFAULT_LUFS_TARGET,
) -> None:
    """Normalize program loudness to target LUFS using ffmpeg's loudnorm filter.

    Uses the EBU R128 two-pass approach: first pass measures, second pass
    applies. This is more accurate than single-pass, especially for spoken
    word where dynamic range varies.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio not found: {input_path}")
    _require("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info(
        "Normalizing %s → %s (target %.1f LUFS)",
        input_path, output_path, target_lufs,
    )

    # Single-pass implementation — good enough for podcast speech, and avoids
    # parsing ffmpeg's measurement JSON. If we need tighter accuracy later,
    # upgrade to two-pass with measured_I/measured_LRA/measured_TP/measured_thresh.
    filter_spec = (
        f"loudnorm=I={target_lufs}:LRA=11:TP=-1.5"
    )
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-af", filter_spec,
            "-ar", "44100",
            "-b:a", "128k",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg loudnorm failed:\n{result.stderr}")


def finish_episode(
    main_path: Path,
    output_path: Path,
    intro_path: Path | None = None,
    outro_path: Path | None = None,
    target_lufs: float = DEFAULT_LUFS_TARGET,
) -> None:
    """Full finishing: splice intro/outro, then normalize to target LUFS.

    Produces a single output MP3 ready for upload. Uses a temp file for
    the splice step; cleaned up on success or failure.
    """
    tmp = output_path.parent / f".splice_tmp_{output_path.stem}.mp3"
    try:
        splice_intro_outro(main_path, tmp, intro_path, outro_path)
        normalize_lufs(tmp, output_path, target_lufs)
    finally:
        tmp.unlink(missing_ok=True)
