"""Tests for split_chunks() — the core text-to-chunks invariant."""
from __future__ import annotations

from auto_podcast_crs.scripts.claude_monologue import split_chunks


def test_basic_split():
    text = "Para one.\n[CHUNK_BREAK]\nPara two."
    assert split_chunks(text) == ["Para one.", "Para two."]


def test_drops_empty_segments():
    text = "\n[CHUNK_BREAK]\n\n[CHUNK_BREAK]\nReal content"
    assert split_chunks(text) == ["Real content"]


def test_strips_whitespace_around_chunks():
    text = "  Para one.  \n[CHUNK_BREAK]\n  Para two.  "
    assert split_chunks(text) == ["Para one.", "Para two."]


def test_no_marker_returns_single_chunk():
    assert split_chunks("Just one paragraph.") == ["Just one paragraph."]


def test_empty_string_returns_empty_list():
    assert split_chunks("") == []


def test_only_markers_returns_empty_list():
    assert split_chunks("[CHUNK_BREAK][CHUNK_BREAK]") == []


def test_preserves_audio_tags_inside_chunks():
    text = "Hello [pauses] world.\n[CHUNK_BREAK]\nNext [emphasizes] idea."
    assert split_chunks(text) == [
        "Hello [pauses] world.",
        "Next [emphasizes] idea.",
    ]
