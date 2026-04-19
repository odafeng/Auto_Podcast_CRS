"""Claude implementation of ScriptAdapter."""
from __future__ import annotations

import logging
from pathlib import Path

from auto_podcast_crs._http import post_with_retry
from auto_podcast_crs.config import get_settings
from auto_podcast_crs.scripts import ScriptAdapter, ScriptResult

log = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CHUNK_MARKER = "[CHUNK_BREAK]"


def split_chunks(text: str, marker: str = CHUNK_MARKER) -> list[str]:
    """Split script text on [CHUNK_BREAK] markers. Drops empty segments."""
    return [c.strip() for c in text.split(marker) if c.strip()]


class ClaudeScriptAdapter(ScriptAdapter):
    """Uses Claude to rewrite blog posts into podcast monologue.

    Default model comes from ANTHROPIC_MODEL env (fallback: claude-sonnet-4-6).
    Override per-instance for A/B prompt/model testing.
    """

    def __init__(
        self,
        prompt_version: str = "v1_generic",
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

    def adapt(self, source_text: str, episode_kind: str = "generic") -> ScriptResult:
        s = get_settings()
        user_prompt = (
            f"Please rewrite the following blog post into a podcast monologue script. "
            f"Episode kind: {episode_kind}.\n\n"
            f"<blog>\n{source_text}\n</blog>"
        )
        log.info(
            "Calling Claude: model=%s prompt=%s src_chars=%d",
            self.model, self.prompt_version, len(source_text),
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
                    "Chunk %d is %d chars — ElevenLabs v3 caps at 3000.", i, len(c)
                )

        return ScriptResult(
            text=text,
            chunks=chunks,
            char_count=len(text),
            metadata={
                "model": self.model,
                "prompt_version": self.prompt_version,
                "usage": usage,
            },
        )
