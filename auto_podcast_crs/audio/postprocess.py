"""Audio post-processing helpers built on ffmpeg."""
import subprocess
from pathlib import Path


def concat_mp3(chunk_paths: list[Path], output_path: Path) -> None:
    """Concat MP3 chunks without re-encoding (lossless, fast)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_list = output_path.parent / f".concat_{output_path.stem}.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in chunk_paths),
        encoding="utf-8",
    )
    try:
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
    return float(result.stdout.strip())
