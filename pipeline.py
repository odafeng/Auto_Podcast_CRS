#!/usr/bin/env python3
"""Entry point for the Auto_Podcast_CRS pipeline.

Usage
-----
    python pipeline.py "The future of renewable energy"
    python pipeline.py --topic "Space exploration in the 21st century"
"""

from __future__ import annotations

import argparse
import logging
import sys

from src.pipeline import PodcastPipeline


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an AI-powered podcast episode from a topic.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "topic",
        nargs="?",
        help="Podcast topic / subject (positional argument)",
    )
    parser.add_argument(
        "--topic",
        dest="topic_flag",
        metavar="TOPIC",
        help="Podcast topic / subject (flag, alternative to positional argument)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    )

    topic = args.topic_flag or args.topic
    if not topic:
        print("Error: please provide a topic.\n", file=sys.stderr)
        print("  python pipeline.py \"The future of AI\"", file=sys.stderr)
        print("  python pipeline.py --topic \"The future of AI\"", file=sys.stderr)
        sys.exit(1)

    pipeline = PodcastPipeline()
    output = pipeline.run(topic)
    print(f"\n✅  Podcast episode saved to: {output}")


if __name__ == "__main__":
    main()
