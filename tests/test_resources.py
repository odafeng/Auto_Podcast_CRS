"""Tests for the resource loader."""
from __future__ import annotations

from pathlib import Path

import pytest

from auto_podcast_crs.scripts.resources import (
    estimate_tokens,
    load_resources,
)


def test_load_from_nonexistent_dir_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_resources(tmp_path / "nope")


def test_load_from_empty_dir_raises(tmp_path: Path):
    (tmp_path / "resources").mkdir()
    with pytest.raises(FileNotFoundError, match="No .md"):
        load_resources(tmp_path / "resources")


def test_load_from_file_path_raises(tmp_path: Path):
    f = tmp_path / "not_a_dir.md"
    f.write_text("content")
    with pytest.raises(NotADirectoryError):
        load_resources(f)


def test_load_single_file(tmp_path: Path):
    d = tmp_path / "resources"
    d.mkdir()
    (d / "paper_a.md").write_text("# Paper A\n\nFindings.")
    bundle = load_resources(d)

    assert len(bundle.resources) == 1
    assert bundle.resources[0].filename == "paper_a.md"
    assert bundle.total_chars > 0
    assert "paper_a.md" in bundle.formatted_context
    assert "Findings." in bundle.formatted_context


def test_load_sorts_by_filename(tmp_path: Path):
    """Stable ordering = reproducible output."""
    d = tmp_path / "resources"
    d.mkdir()
    (d / "zzz_last.md").write_text("zzz content")
    (d / "aaa_first.md").write_text("aaa content")
    (d / "mmm_middle.md").write_text("mmm content")
    bundle = load_resources(d)

    filenames = [r.filename for r in bundle.resources]
    assert filenames == ["aaa_first.md", "mmm_middle.md", "zzz_last.md"]


def test_load_skips_non_markdown_files(tmp_path: Path):
    d = tmp_path / "resources"
    d.mkdir()
    (d / "paper.md").write_text("keep this")
    (d / "image.png").write_bytes(b"\x89PNG")  # should be skipped
    (d / "notes.pdf").write_bytes(b"%PDF-")      # should be skipped
    bundle = load_resources(d)

    filenames = [r.filename for r in bundle.resources]
    assert filenames == ["paper.md"]


def test_load_accepts_txt_and_markdown_extensions(tmp_path: Path):
    d = tmp_path / "resources"
    d.mkdir()
    (d / "a.md").write_text("md")
    (d / "b.markdown").write_text("markdown")
    (d / "c.txt").write_text("txt")
    bundle = load_resources(d)

    assert len(bundle.resources) == 3


def test_load_respects_token_budget(tmp_path: Path):
    d = tmp_path / "resources"
    d.mkdir()
    # 10k chars ≈ 6.6k estimated tokens. Budget of 5000 tokens → fails.
    (d / "big.md").write_text("A" * 10_000)

    with pytest.raises(ValueError, match="exceed budget"):
        load_resources(d, token_budget=5_000)


def test_load_within_budget_succeeds(tmp_path: Path):
    d = tmp_path / "resources"
    d.mkdir()
    (d / "small.md").write_text("A" * 100)

    bundle = load_resources(d, token_budget=1_000)
    assert bundle.total_chars == 100


def test_formatted_context_uses_xml_tags(tmp_path: Path):
    d = tmp_path / "resources"
    d.mkdir()
    (d / "paper.md").write_text("research content")
    bundle = load_resources(d)

    ctx = bundle.formatted_context
    assert "<resources>" in ctx
    assert "</resources>" in ctx
    assert '<source name="paper.md">' in ctx
    assert "</source>" in ctx


def test_estimate_tokens_rough():
    assert estimate_tokens("") == 0
    assert estimate_tokens("A" * 15) == 10  # 15 / 1.5
