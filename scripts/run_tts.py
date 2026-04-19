"""CLI: run TTS on a generated script.

Usage:
    python scripts/run_tts.py --episode 04
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auto_podcast_crs.audio import concat_mp3, get_audio_duration
from auto_podcast_crs.tts.elevenlabs_v3 import ElevenLabsV3TTS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True, help="Episode folder name")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    episode_dir = repo_root / "episodes" / args.episode
    script_path = episode_dir / "script.txt"

    if not script_path.exists():
        print(f"Script not found: {script_path}. Run generate_script.py first.", file=sys.stderr)
        sys.exit(1)

    script = script_path.read_text(encoding="utf-8").strip()
    chunks = [c.strip() for c in script.split("[CHUNK_BREAK]") if c.strip()]

    print(f"Episode: {args.episode}")
    print(f"Chunks:  {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"  chunk {i}: {len(c)} chars")

    work_dir = episode_dir / "tts_chunks"
    output_path = episode_dir / f"{args.episode}_full.mp3"

    tts = ElevenLabsV3TTS()
    result = tts.synthesize(chunks, output_dir=work_dir)

    concat_mp3(result.chunk_paths, output_path)
    duration = get_audio_duration(output_path)
    size_mb = output_path.stat().st_size / (1024 * 1024)

    print(f"\n=== Done ===")
    print(f"Output:   {output_path}")
    print(f"Duration: {duration:.1f}s ({duration/60:.1f} min)")
    print(f"Size:     {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
