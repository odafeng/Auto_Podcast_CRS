"""Publish an episode: finish audio → upload to R2 → rebuild feed → upload feed.

This is the glue that makes the pipeline actually end-to-end. Each step is a
thin wrapper around the module that does the real work; the value of this
file is the sequencing and error surfaces.

Steps:
  1. Locate episode folder + load metadata.yaml
  2. Finish audio: splice intro/outro, normalize to target LUFS
  3. Upload finished MP3 to R2
  4. Scan all episodes for ones with a public audio_url → rebuild feed.xml
  5. Upload feed.xml to R2

Idempotent: re-running on a published episode re-uploads (overwrite).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

from auto_podcast_crs.audio import finish_episode, get_audio_duration
from auto_podcast_crs.config import get_settings
from auto_podcast_crs.rss import EpisodeMetadata, ShowMetadata, build_rss_feed
from auto_podcast_crs.storage.r2 import R2Storage

log = logging.getLogger(__name__)

DEFAULT_FEED_KEY = "feed.xml"


@dataclass(frozen=True)
class PublishResult:
    episode_slug: str
    audio_url: str
    feed_url: str
    finished_audio_path: Path
    feed_xml_path: Path


def publish_episode(
    episode_dir: Path,
    *,
    intro_path: Path | None = None,
    outro_path: Path | None = None,
    target_lufs: float = -16.0,
    show: ShowMetadata | None = None,
    episodes_root: Path | None = None,
) -> PublishResult:
    """Run the full publish pipeline for one episode.

    Args:
        episode_dir: Path to the episode folder (contains metadata.yaml +
            `<episode_id>_full.mp3` from run_tts.py).
        intro_path / outro_path: Optional audio to splice in.
        target_lufs: Loudness target (default -16.0 = Apple/Spotify spec).
        show: Show metadata. If None, loaded from brand/metadata.md via
            load_show_metadata() (see below — that loader is stubbed).
        episodes_root: Where to scan for all episodes when rebuilding feed.
            Defaults to settings.episodes_dir.
    """
    s = get_settings()
    if episodes_root is None:
        episodes_root = s.episodes_dir
    if show is None:
        show = load_show_metadata()

    meta_path = episode_dir / "metadata.yaml"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.yaml not found in {episode_dir}")
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))

    slug = meta["slug"]
    episode_id = f"{meta['episode']}_{slug}"

    # 1. Locate raw audio (from run_tts.py output)
    raw_audio = episode_dir / f"{episode_id}_full.mp3"
    if not raw_audio.exists():
        # Fall back to older naming convention
        raw_audio = episode_dir / f"{meta['episode']}_full.mp3"
    if not raw_audio.exists():
        raise FileNotFoundError(
            f"Raw audio not found in {episode_dir} "
            f"(tried {episode_id}_full.mp3 and {meta['episode']}_full.mp3)"
        )

    # 2. Finish audio
    finished_path = episode_dir / f"{episode_id}_final.mp3"
    log.info("[1/4] Finishing audio for %s", episode_id)
    finish_episode(
        main_path=raw_audio,
        output_path=finished_path,
        intro_path=intro_path,
        outro_path=outro_path,
        target_lufs=target_lufs,
    )
    duration_s = int(round(get_audio_duration(finished_path)))
    size_bytes = finished_path.stat().st_size

    # 3. Upload to R2
    storage = R2Storage()
    audio_key = f"episodes/{episode_id}.mp3"
    log.info("[2/4] Uploading %s to R2", audio_key)
    audio_url = storage.upload(finished_path, audio_key, content_type="audio/mpeg")

    # 4. Update metadata.yaml in-place with audio_url + published
    meta["audio"] = {
        "url": audio_url,
        "duration_seconds": duration_s,
        "size_bytes": size_bytes,
    }
    if meta.get("published") is None:
        meta["published"] = datetime.now(UTC).isoformat()
    meta_path.write_text(
        yaml.safe_dump(meta, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    # 5. Rebuild feed from ALL episodes that have an audio_url
    log.info("[3/4] Rebuilding feed.xml from all published episodes")
    all_episodes = _collect_published_episodes(episodes_root)
    feed_path = episodes_root.parent / "feed.xml"
    build_rss_feed(show, all_episodes, feed_path)

    # 6. Upload feed.xml
    log.info("[4/4] Uploading feed.xml to R2")
    feed_url = storage.upload(feed_path, DEFAULT_FEED_KEY, content_type="application/rss+xml")

    log.info("=== Published %s ===", episode_id)
    log.info("Audio: %s", audio_url)
    log.info("Feed:  %s", feed_url)

    return PublishResult(
        episode_slug=slug,
        audio_url=audio_url,
        feed_url=feed_url,
        finished_audio_path=finished_path,
        feed_xml_path=feed_path,
    )


def _collect_published_episodes(episodes_root: Path) -> list[EpisodeMetadata]:
    """Scan episodes/ for metadata.yaml files with an audio.url set."""
    collected: list[EpisodeMetadata] = []
    for meta_path in sorted(episodes_root.glob("*/metadata.yaml")):
        try:
            m = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            log.warning("Skipping %s: %s", meta_path, e)
            continue
        audio = m.get("audio") or {}
        if not audio.get("url"):
            continue

        published_raw = m.get("published")
        if isinstance(published_raw, str):
            try:
                published = datetime.fromisoformat(published_raw)
            except ValueError:
                log.warning("Bad published date in %s: %r", meta_path, published_raw)
                continue
        elif isinstance(published_raw, datetime):
            published = published_raw
        else:
            log.warning("Episode %s has audio but no published date; skipping", meta_path)
            continue

        collected.append(EpisodeMetadata(
            episode_number=int(m["episode"]),
            title=m.get("title_zh") or m["slug"],
            description=m.get("notes") or m.get("title_en") or "",
            audio_url=audio["url"],
            audio_size_bytes=int(audio.get("size_bytes", 0)),
            duration_seconds=int(audio.get("duration_seconds", 0)),
            published=published,
            slug=m["slug"],
        ))
    return collected


def load_show_metadata() -> ShowMetadata:
    """Load show-level metadata from brand/metadata.md + env.

    brand/metadata.md is human-readable (Markdown), not YAML. For v1 we hardcode
    the known-good values here and flag this as TODO for a proper loader. This
    is deliberate — the brand metadata changes rarely and parsing prose MD is
    a footgun.
    """
    s = get_settings()
    return ShowMetadata(
        title="腸所欲言 ColonClub",
        subtitle="一個大腸直腸外科醫師的 open mic",
        description=(
            "腸所欲言是一個中文大腸直腸外科 podcast。由主治醫師黃士峯主持，"
            "內容涵蓋臨床新知、手術經驗、Surgical Data Science、程式入門，"
            "以及身為一個「開刀也寫 code」的醫師在這個路上的真實記錄。"
        ),
        author="黃士峯 Shih-Feng Huang, MD",
        language="zh-TW",
        owner_name="黃士峯",
        owner_email="odafeng@hotmail.com",
        category="Health & Fitness",
        subcategory="Medicine",
        explicit=False,
        artwork_url=f"{s.r2_public_url.rstrip('/')}/artwork.jpg",
        site_url="https://shihfenghuang.com",
        feed_url=f"{s.r2_public_url.rstrip('/')}/feed.xml",
    )
