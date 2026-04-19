"""CLI: generate a podcast script from a blog post.

Usage:
    python scripts/generate_script.py \
        --episode 04 \
        --blog-path episodes/04_xxx/source.md \
        --prompt-version v1_generic
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auto_podcast_crs.scripts.claude_monologue import ClaudeScriptAdapter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True, help="Episode folder name (e.g. '04_xxx')")
    parser.add_argument("--blog-path", type=Path, help="Path to blog source .md file")
    parser.add_argument(
        "--prompt-version",
        default="v1_generic",
        choices=["v1_generic", "v1_persuasion", "v1_onboarding"],
        help="Which prompt template to use",
    )
    parser.add_argument(
        "--episode-kind",
        default="generic",
        help="Episode kind hint passed to the adapter",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    episode_dir = repo_root / "episodes" / args.episode
    episode_dir.mkdir(parents=True, exist_ok=True)

    source_path = args.blog_path or (episode_dir / "source.md")
    if not source_path.exists():
        print(f"Source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    source_text = source_path.read_text(encoding="utf-8")
    print(f"Loaded source: {len(source_text)} chars from {source_path}")

    adapter = ClaudeScriptAdapter(prompt_version=args.prompt_version)
    result = adapter.adapt(source_text, episode_kind=args.episode_kind)

    out_path = episode_dir / "script.txt"
    out_path.write_text(result.text, encoding="utf-8")

    print(f"\n=== Script generated ===")
    print(f"Chars:  {result.char_count}")
    print(f"Chunks: {len(result.chunks)}")
    print(f"Usage:  {result.metadata['usage']}")
    print(f"Saved:  {out_path}")


if __name__ == "__main__":
    main()
