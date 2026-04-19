"""Loader for per-episode resource files.

Usage pattern: user drops 2-5 relevant .md files into
  episodes/<id>/resources/
before generating a topic-based episode. This loader concatenates them into
a single prompt-ready string with clear file boundaries, and guards against
accidentally blowing out the context window.

Design choices:
- Markdown only for now. PDFs can be added later via a separate pdf-reader
  step that writes the extracted text back to the resources dir as .md.
- Conservative character-to-token estimation (1.5 chars/token for mixed
  Chinese/English, which is a slightly pessimistic default).
- Hard cap at 400k estimated tokens (half of Claude Sonnet 4.6's 1M context,
  leaving ample room for system prompt + output).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

# 1.5 chars/token is a conservative mixed-language estimate. For pure English,
# the real ratio is closer to 4; for pure Chinese, closer to 1.5. Erring on
# the side of assuming more tokens protects us from context overflow.
CHARS_PER_TOKEN_ESTIMATE = 1.5

# Half the context window of Claude Sonnet 4.6 (1M). Leaves room for system
# prompt (~3k), user instructions (~2k), and output (~8k).
DEFAULT_TOKEN_BUDGET = 400_000

RESOURCE_EXTENSIONS = {".md", ".markdown", ".txt"}


@dataclass(frozen=True)
class LoadedResource:
    """A single resource file that was included in the context."""
    path: Path
    filename: str
    char_count: int
    estimated_tokens: int


@dataclass(frozen=True)
class ResourceBundle:
    """All loaded resources ready for inclusion in a prompt."""
    resources: list[LoadedResource]
    formatted_context: str  # the XML-tagged block to paste into the prompt
    total_chars: int
    total_estimated_tokens: int


def estimate_tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN_ESTIMATE)


def load_resources(
    resources_dir: Path,
    *,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
) -> ResourceBundle:
    """Load all markdown/txt files from resources_dir into a prompt-ready bundle.

    Files are sorted by filename (stable ordering = reproducible output).
    Raises if the total exceeds token_budget — curation is the user's job.
    """
    if not resources_dir.exists():
        raise FileNotFoundError(
            f"Resources directory does not exist: {resources_dir}\n"
            f"Create it and drop 2-5 relevant .md files before running this."
        )
    if not resources_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {resources_dir}")

    files = sorted(
        p for p in resources_dir.iterdir()
        if p.is_file() and p.suffix.lower() in RESOURCE_EXTENSIONS
    )
    if not files:
        raise FileNotFoundError(
            f"No .md/.markdown/.txt files in {resources_dir}\n"
            f"Drop at least one resource file before running this."
        )

    loaded: list[LoadedResource] = []
    total_chars = 0
    total_tokens = 0

    for f in files:
        text = f.read_text(encoding="utf-8")
        chars = len(text)
        tokens = estimate_tokens(text)
        loaded.append(LoadedResource(
            path=f, filename=f.name, char_count=chars, estimated_tokens=tokens,
        ))
        total_chars += chars
        total_tokens += tokens
        log.info(
            "Loaded resource: %s (%d chars, ~%d tokens)",
            f.name, chars, tokens,
        )

    if total_tokens > token_budget:
        raise ValueError(
            f"Total resource tokens ({total_tokens:,}) exceed budget "
            f"({token_budget:,}). Curate the files in {resources_dir} "
            f"— drop some, summarize large ones, or split into multiple "
            f"episodes."
        )

    formatted_context = _format_resources(loaded)
    log.info(
        "Resource bundle: %d file(s), %d chars, ~%d tokens",
        len(loaded), total_chars, total_tokens,
    )

    return ResourceBundle(
        resources=loaded,
        formatted_context=formatted_context,
        total_chars=total_chars,
        total_estimated_tokens=total_tokens,
    )


def _format_resources(loaded: list[LoadedResource]) -> str:
    """Format loaded resources as XML-tagged blocks.

    Claude handles XML-tagged documents well and can reference by filename.
    The <source name="..."> tag lets the prompt instruct Claude to attribute
    facts by source.
    """
    blocks: list[str] = []
    for r in loaded:
        content = r.path.read_text(encoding="utf-8").strip()
        blocks.append(
            f'<source name="{r.filename}">\n{content}\n</source>'
        )
    return "<resources>\n" + "\n\n".join(blocks) + "\n</resources>"
