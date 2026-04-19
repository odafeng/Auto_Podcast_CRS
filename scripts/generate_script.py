"""CLI: generate a podcast script from a blog post.

Usage:
    python scripts/generate_script.py \
        --episode 04_xxx \
        --blog-path episodes/04_xxx/source.md \
        --prompt-version v1_generic
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auto_podcast_crs._logging import setup_logging  # noqa: E402
from auto_podcast_crs.scripts.claude_monologue import ClaudeScriptAdapter  # noqa: E402

log = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True, help="Episode folder name (e.g. '04_xxx')")
    parser.add_argument("--blog-path", type=Path, help="Path to blog source .md file")
    parser.add_argument(
        "--prompt-version",
        default="v2_generic",
        choices=[
            "v1_generic", "v1_persuasion", "v1_onboarding",
            "v2_generic", "v2_persuasion", "v2_onboarding",
        ],
        help="Which prompt template to use (default: v2_generic)",
    )
    parser.add_argument(
        "--episode-kind",
        default="generic",
        help="Episode kind hint passed to the adapter",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="DEBUG|INFO|WARNING|ERROR (default: INFO or $AUTOPODCAST_LOG_LEVEL)",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    repo_root = Path(__file__).resolve().parent.parent
    episode_dir = repo_root / "episodes" / args.episode
    episode_dir.mkdir(parents=True, exist_ok=True)

    source_path = args.blog_path or (episode_dir / "source.md")
    if not source_path.exists():
        log.error("Source file not found: %s", source_path)
        return 1

    source_text = source_path.read_text(encoding="utf-8")
    log.info("Loaded source: %d chars from %s", len(source_text), source_path)

    adapter = ClaudeScriptAdapter(prompt_version=args.prompt_version)
    result = adapter.adapt(source_text, episode_kind=args.episode_kind)

    out_path = episode_dir / "script.txt"
    out_path.write_text(result.text, encoding="utf-8")

    log.info("=== Script generated ===")
    log.info("Chars:  %d", result.char_count)
    log.info("Chunks: %d", len(result.chunks))
    log.info("Usage:  %s", result.metadata.get("usage"))
    log.info("Saved:  %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
