"""Build iTunes-spec RSS feed XML for the podcast.

Apple spec: https://help.apple.com/itc/podcasts_connect/#/itcb54353390

We use feedgen (https://feedgen.kiesow.be) because rolling our own XML for
iTunes namespace is a rabbit hole of subtle breakage. feedgen handles the
`<itunes:category>`, `<itunes:explicit>`, `<enclosure>`, and CDATA wrapping
correctly.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ShowMetadata:
    """Podcast-level metadata (set once per show)."""
    title: str
    subtitle: str
    description: str
    author: str
    language: str  # "zh-TW" etc.
    owner_name: str
    owner_email: str
    category: str  # primary Apple category, e.g. "Health & Fitness"
    subcategory: str | None  # e.g. "Medicine"
    explicit: bool
    artwork_url: str  # 1400–3000 px square JPG/PNG URL
    site_url: str  # show homepage
    feed_url: str  # canonical RSS URL (where this feed lives after upload)


@dataclass(frozen=True)
class EpisodeMetadata:
    """Per-episode metadata used to render a single `<item>`."""
    episode_number: int
    title: str
    description: str
    audio_url: str  # public MP3 URL
    audio_size_bytes: int
    duration_seconds: int
    published: datetime  # publish date, ideally timezone-aware UTC
    slug: str
    author: str | None = None


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware; assume UTC if naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def build_rss_feed(
    show: ShowMetadata,
    episodes: list[EpisodeMetadata],
    output_path: Path,
) -> None:
    """Render episodes → iTunes-spec RSS XML at output_path.

    Episodes are sorted by `published` descending (newest first), per RSS
    convention.
    """
    try:
        from feedgen.feed import FeedGenerator
    except ImportError as e:
        raise RuntimeError(
            "feedgen not installed. Install with: pip install -e '.[rss]'"
        ) from e

    fg = FeedGenerator()
    fg.load_extension("podcast")

    fg.title(show.title)
    fg.link(href=show.site_url, rel="alternate")
    fg.link(href=show.feed_url, rel="self")
    fg.description(show.description)
    fg.language(show.language)
    fg.author({"name": show.author, "email": show.owner_email})
    fg.logo(show.artwork_url)
    fg.image(show.artwork_url)

    # iTunes-specific tags
    fg.podcast.itunes_author(show.author)
    fg.podcast.itunes_summary(show.description)
    fg.podcast.itunes_subtitle(show.subtitle)
    fg.podcast.itunes_owner(name=show.owner_name, email=show.owner_email)
    fg.podcast.itunes_explicit("yes" if show.explicit else "no")
    fg.podcast.itunes_image(show.artwork_url)
    if show.subcategory:
        fg.podcast.itunes_category(show.category, show.subcategory)
    else:
        fg.podcast.itunes_category(show.category)

    # Episodes: feedgen.add_entry() prepends by default, so iterate
    # oldest-first — the final rendered order will be newest-first.
    for ep in sorted(episodes, key=lambda e: e.published):
        fe = fg.add_entry()
        ep_author = ep.author or show.author
        fe.id(ep.audio_url)
        fe.title(ep.title)
        fe.description(ep.description)
        fe.author({"name": ep_author, "email": show.owner_email})
        fe.pubDate(_ensure_utc(ep.published))
        fe.enclosure(ep.audio_url, str(ep.audio_size_bytes), "audio/mpeg")
        fe.podcast.itunes_author(ep_author)
        fe.podcast.itunes_duration(_format_duration(ep.duration_seconds))
        fe.podcast.itunes_episode(ep.episode_number)
        fe.podcast.itunes_explicit("no")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fg.rss_file(str(output_path), pretty=True)
    log.info(
        "Wrote RSS feed: %s (%d episodes)", output_path, len(episodes),
    )


def _format_duration(total_seconds: int) -> str:
    """Format seconds as HH:MM:SS or MM:SS (iTunes accepts both)."""
    h, rem = divmod(int(total_seconds), 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"
