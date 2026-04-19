"""Topic+resources implementation — generate an original script from a
topic string plus a bundle of reference documents.

Different contract from ScriptAdapter (which expects a single source_text
to adapt). Kept as a separate class rather than forced into the same ABC
because the inputs, prompts, and output metadata all differ.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from auto_podcast_crs._http import post_with_retry
from auto_podcast_crs.config import get_settings
from auto_podcast_crs.scripts.claude_monologue import (
    CLAUDE_API_URL,
    PROMPTS_DIR,
    split_chunks,
)
from auto_podcast_crs.scripts.resources import ResourceBundle

log = logging.getLogger(__name__)


@dataclass
class TopicScriptResult:
    text: str
    chunks: list[str]
    char_count: int
    resources_used: list[str]  # filenames
    resource_char_total: int
    metadata: dict


class TopicScriptAdapter:
    """Synthesize an original podcast script from topic + resources."""

    def __init__(
        self,
        prompt_version: str = "v3_topic_generic",
        model: str | None = None,
        max_tokens: int | None = None,
    ):
        self.prompt_version = prompt_version
        s = get_settings()
        self.model = model or s.anthropic_model
        self.max_tokens = max_tokens or s.anthropic_max_tokens

        prompt_path = PROMPTS_DIR / f"system_{prompt_version}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

        if not s.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

    def generate(
        self,
        topic: str,
        resources: ResourceBundle,
        *,
        angle: str | None = None,
    ) -> TopicScriptResult:
        """Generate a script from topic + resources.

        Args:
            topic: What this episode is about (one sentence or a short brief).
            resources: Pre-loaded resource bundle (see resources.load_resources).
            angle: Optional extra framing, e.g. "focus on trainee perspective".
        """
        s = get_settings()

        topic = topic.strip()
        if not topic:
            raise ValueError("topic must not be empty")

        # Assemble user message: topic + optional angle + resources context
        parts: list[str] = [
            f"<topic>\n{topic}\n</topic>",
        ]
        if angle:
            parts.append(f"<angle>\n{angle.strip()}\n</angle>")
        parts.append(resources.formatted_context)
        parts.append(
            "根據上面的主題和資料,寫一集 podcast 獨白腳本。\n"
            "遵守 system prompt 裡的所有風格規則和禁令。\n"
            "只輸出腳本本體,不要前言或 references 清單。"
        )
        user_prompt = "\n\n".join(parts)

        log.info(
            "Calling Claude: model=%s prompt=%s topic_chars=%d "
            "resource_files=%d resource_chars=%d",
            self.model, self.prompt_version, len(topic),
            len(resources.resources), resources.total_chars,
        )

        response = post_with_retry(
            CLAUDE_API_URL,
            headers={
                "x-api-key": s.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": self.system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=180,
        )
        data = response.json()
        text = data["content"][0]["text"]
        chunks = split_chunks(text)
        usage = data.get("usage", {})

        log.info(
            "Claude response: out_chars=%d chunks=%d in_tok=%s out_tok=%s",
            len(text), len(chunks),
            usage.get("input_tokens"), usage.get("output_tokens"),
        )
        for i, c in enumerate(chunks):
            if len(c) > 3000:
                log.warning(
                    "Chunk %d is %d chars — ElevenLabs v3 caps at 3000.",
                    i, len(c),
                )

        # Guardrail: warn if any resource content appears verbatim in output.
        # Paraphrasing is required; copy-paste is forbidden.
        _warn_on_verbatim_copy(text, resources)

        return TopicScriptResult(
            text=text,
            chunks=chunks,
            char_count=len(text),
            resources_used=[r.filename for r in resources.resources],
            resource_char_total=resources.total_chars,
            metadata={
                "model": self.model,
                "prompt_version": self.prompt_version,
                "usage": usage,
                "topic": topic,
                "angle": angle,
            },
        )


# Minimum length of consecutive characters to flag as a likely verbatim copy.
# 40 chars of Chinese ≈ one long sentence; below this, false positives from
# common phrases are too frequent.
_VERBATIM_FLAG_LEN = 40


def _warn_on_verbatim_copy(script_text: str, resources: ResourceBundle) -> None:
    """Log a warning for any 40+ char run that appears verbatim in a resource.

    This is a guard rail, not a blocker — the v3 prompt explicitly forbids
    verbatim copy, and we want visibility when the model violates it.
    """
    for r in resources.resources:
        resource_text = r.path.read_text(encoding="utf-8")
        # Scan script for windows that match resource verbatim.
        # Simple O(n*m) scan is fine for podcast-scale (few thousand chars).
        hits = 0
        for i in range(len(script_text) - _VERBATIM_FLAG_LEN):
            window = script_text[i:i + _VERBATIM_FLAG_LEN]
            if window in resource_text:
                hits += 1
                if hits <= 3:  # log at most 3 per resource
                    log.warning(
                        "Possible verbatim copy from %s: %r",
                        r.filename, window,
                    )
        if hits > 3:
            log.warning(
                "%d total verbatim matches from %s (first 3 shown)",
                hits, r.filename,
            )


# Re-export for callers that want to access the prompt path
__all__ = ["TopicScriptAdapter", "TopicScriptResult", "PROMPTS_DIR"]


# noqa needed because we re-import PROMPTS_DIR from claude_monologue for
# external consumers — the __all__ entry makes that explicit.
