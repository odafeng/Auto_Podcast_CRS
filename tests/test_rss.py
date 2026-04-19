"""Tests for RSS feed builder."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

pytest.importorskip("feedgen")

from auto_podcast_crs.rss import EpisodeMetadata, ShowMetadata, build_rss_feed  # noqa: E402


def _show() -> ShowMetadata:
    return ShowMetadata(
        title="腸所欲言 ColonClub",
        subtitle="test subtitle",
        description="test description",
        author="Test Author",
        language="zh-TW",
        owner_name="Test Owner",
        owner_email="test@example.com",
        category="Health & Fitness",
        subcategory="Medicine",
        explicit=False,
        artwork_url="https://example.com/art.jpg",
        site_url="https://example.com",
        feed_url="https://example.com/feed.xml",
    )


def _episode(num: int, published: datetime) -> EpisodeMetadata:
    return EpisodeMetadata(
        episode_number=num,
        title=f"Episode {num}",
        description=f"Description {num}",
        audio_url=f"https://example.com/ep{num}.mp3",
        audio_size_bytes=1_500_000,
        duration_seconds=480,
        published=published,
        slug=f"ep{num}",
    )


def test_build_rss_produces_valid_xml(tmp_path: Path):
    out = tmp_path / "feed.xml"
    episodes = [
        _episode(1, datetime(2026, 4, 1, tzinfo=UTC)),
        _episode(2, datetime(2026, 4, 8, tzinfo=UTC)),
    ]
    build_rss_feed(_show(), episodes, out)

    xml = out.read_text(encoding="utf-8")
    assert "<?xml" in xml
    assert "<rss" in xml
    assert "腸所欲言" in xml
    assert "https://example.com/ep1.mp3" in xml
    assert "https://example.com/ep2.mp3" in xml


def test_rss_orders_newest_first(tmp_path: Path):
    out = tmp_path / "feed.xml"
    episodes = [
        _episode(1, datetime(2026, 4, 1, tzinfo=UTC)),
        _episode(2, datetime(2026, 4, 8, tzinfo=UTC)),
        _episode(3, datetime(2026, 4, 15, tzinfo=UTC)),
    ]
    build_rss_feed(_show(), episodes, out)
    xml = out.read_text(encoding="utf-8")

    # ep3 should appear before ep1 in the XML
    assert xml.index("ep3.mp3") < xml.index("ep2.mp3") < xml.index("ep1.mp3")


def test_rss_includes_itunes_namespace(tmp_path: Path):
    out = tmp_path / "feed.xml"
    build_rss_feed(_show(), [], out)
    xml = out.read_text(encoding="utf-8")
    assert "xmlns:itunes" in xml
    assert "<itunes:category" in xml
    assert "Medicine" in xml  # subcategory


def test_rss_handles_naive_datetime(tmp_path: Path):
    """Naive datetimes should be treated as UTC, not error."""
    out = tmp_path / "feed.xml"
    ep = _episode(1, datetime(2026, 4, 1))  # no tz
    build_rss_feed(_show(), [ep], out)
    assert out.exists()


def test_rss_empty_episode_list_still_writes(tmp_path: Path):
    out = tmp_path / "feed.xml"
    build_rss_feed(_show(), [], out)
    xml = out.read_text(encoding="utf-8")
    assert "<?xml" in xml
    # No <item> tags
    assert "<item>" not in xml
