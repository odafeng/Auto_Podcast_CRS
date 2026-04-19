"""CLI: generate a podcast script from a topic + per-episode resources.

Usage:
    mkdir -p episodes/04_my-slug/resources
    # drop 2-5 relevant .md files into episodes/04_my-slug/resources/

    python scripts/generate_from_topic.py \\
        --episode 04_my-slug \\
        --topic "robotic colorectal surgery learning curve 怎麼評估"

Output:
    episodes/04_my-slug/script.txt
    episodes/04_my-slug/sources_used.yaml  (audit trail)
    episodes/04_my-slug/metadata.yaml       (created if absent, updated if present)
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auto_podcast_crs._logging import setup_logging  # noqa: E402
from auto_podcast_crs.scripts.resources import load_resources  # noqa: E402
from auto_podcast_crs.scripts.topic_to_script import TopicScriptAdapter  # noqa: E402

log = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True, help="Episode folder name (e.g. '04_xxx')")
    parser.add_argument("--topic", required=True, help="Topic for this episode")
    parser.add_argument(
        "--angle",
        default=None,
        help="Optional extra framing (e.g. 'focus on trainee perspective')",
    )
    parser.add_argument(
        "--prompt-version",
        default="v3_topic_generic",
        help="Which v3 prompt to use (default: v3_topic_generic)",
    )
    parser.add_argument(
        "--resources-dir",
        type=Path,
        default=None,
        help="Override resources dir (default: episodes/<episode>/resources/)",
    )
    parser.add_argument("--log-level", default=None)
    args = parser.parse_args()

    setup_logging(args.log_level)

    repo_root = Path(__file__).resolve().parent.parent
    episode_dir = repo_root / "episodes" / args.episode
    episode_dir.mkdir(parents=True, exist_ok=True)

    resources_dir = args.resources_dir or (episode_dir / "resources")

    # Load resources (errors out clearly if empty or over budget)
    try:
        bundle = load_resources(resources_dir)
    except (FileNotFoundError, ValueError, NotADirectoryError) as e:
        log.error("Resource load failed: %s", e)
        return 1

    # Generate
    adapter = TopicScriptAdapter(prompt_version=args.prompt_version)
    try:
        result = adapter.generate(args.topic, bundle, angle=args.angle)
    except Exception:
        log.exception("Script generation failed")
        return 1

    # Write script
    script_path = episode_dir / "script.txt"
    script_path.write_text(result.text, encoding="utf-8")

    # Audit trail: which files were used, their sizes, timestamp
    audit = {
        "generated_at": datetime.now(UTC).isoformat(),
        "topic": args.topic,
        "angle": args.angle,
        "prompt_version": args.prompt_version,
        "model": result.metadata.get("model"),
        "usage": result.metadata.get("usage"),
        "script_char_count": result.char_count,
        "script_chunks": len(result.chunks),
        "resources": [
            {"filename": r.filename, "char_count": r.char_count}
            for r in bundle.resources
        ],
        "resource_char_total": bundle.total_chars,
    }
    audit_path = episode_dir / "sources_used.yaml"
    audit_path.write_text(
        yaml.safe_dump(audit, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    # Update metadata.yaml (create if absent)
    meta_path = episode_dir / "metadata.yaml"
    if meta_path.exists():
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    else:
        meta = {
            "episode": args.episode.split("_")[0],
            "slug": "_".join(args.episode.split("_")[1:]) or args.episode,
        }
    meta["source"] = {
        "type": "topic_plus_resources",
        "topic": args.topic,
        "resources_used": result.resources_used,
        "resource_char_count": bundle.total_chars,
    }
    meta["script"] = {
        "prompt_version": args.prompt_version,
        "char_count": result.char_count,
        "chunks": len(result.chunks),
    }
    meta_path.write_text(
        yaml.safe_dump(meta, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    log.info("=== Script generated ===")
    log.info("Topic:     %s", args.topic)
    log.info("Resources: %d file(s), %d chars", len(bundle.resources), bundle.total_chars)
    log.info("Script:    %d chars, %d chunks", result.char_count, len(result.chunks))
    log.info("Usage:     %s", result.metadata.get("usage"))
    log.info("Saved:     %s", script_path)
    log.info("Audit:     %s", audit_path)
    log.info("")
    log.info("Review the script, then run:")
    log.info("  python scripts/run_tts.py --episode %s", args.episode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
