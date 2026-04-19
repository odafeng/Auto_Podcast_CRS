"""CLI: publish an episode end-to-end.

Usage:
    python scripts/publish.py --episode 04_xxx \
        [--intro static/intro.mp3] \
        [--outro static/outro.mp3] \
        [--target-lufs -16.0]

Prerequisites:
    - `python scripts/run_tts.py --episode <slug>` has been run first
      (produces the raw `<episode_id>_full.mp3`).
    - R2 credentials set in env (R2_ENDPOINT, R2_ACCESS_KEY_ID, etc).
    - pip install -e '.[storage,rss]'
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auto_podcast_crs._logging import setup_logging  # noqa: E402
from auto_podcast_crs.pipeline import publish_episode  # noqa: E402

log = logging.getLogger(__name__)


def _resolve_audio_path(flag_value: str | None, env_var: str) -> Path | None:
    """Priority: CLI flag > env var > None. Validates existence if set."""
    raw = flag_value or os.environ.get(env_var)
    if not raw:
        return None
    p = Path(raw)
    if not p.exists():
        log.warning("%s=%s does not exist; continuing without it", env_var, p)
        return None
    return p


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True, help="Episode folder name")
    parser.add_argument("--intro", default=None, help="Path to intro.mp3 (optional)")
    parser.add_argument("--outro", default=None, help="Path to outro.mp3 (optional)")
    parser.add_argument("--target-lufs", type=float, default=-16.0)
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()

    setup_logging(args.log_level)

    repo_root = Path(__file__).resolve().parent.parent
    episode_dir = repo_root / "episodes" / args.episode
    if not episode_dir.exists():
        log.error("Episode dir not found: %s", episode_dir)
        return 1

    intro = _resolve_audio_path(args.intro, "INTRO_MP3_PATH")
    outro = _resolve_audio_path(args.outro, "OUTRO_MP3_PATH")

    try:
        result = publish_episode(
            episode_dir=episode_dir,
            intro_path=intro,
            outro_path=outro,
            target_lufs=args.target_lufs,
        )
    except Exception:
        log.exception("Publish failed")
        return 1

    log.info("")
    log.info("=== Publish succeeded ===")
    log.info("Audio URL: %s", result.audio_url)
    log.info("Feed URL:  %s", result.feed_url)
    log.info("")
    log.info(
        "Next step: if this is your first episode, submit %s to Apple Podcasts "
        "Connect and Spotify for Creators. Apple takes up to 24h to poll.",
        result.feed_url,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
