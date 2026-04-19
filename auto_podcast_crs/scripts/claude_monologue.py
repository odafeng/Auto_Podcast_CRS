"""Claude Sonnet implementation of ScriptAdapter."""
from pathlib import Path

import requests

from auto_podcast_crs.config import settings
from auto_podcast_crs.scripts import ScriptAdapter, ScriptResult

PROMPTS_DIR = Path(__file__).parent / "prompts"


class ClaudeScriptAdapter(ScriptAdapter):
    """Uses Claude Sonnet 4.6 to rewrite blog posts into podcast monologue."""

    def __init__(self, prompt_version: str = "v1_generic"):
        self.prompt_version = prompt_version
        prompt_path = PROMPTS_DIR / f"system_{prompt_version}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    def adapt(self, source_text: str, episode_kind: str = "generic") -> ScriptResult:
        user_prompt = (
            f"Please rewrite the following blog post into a podcast monologue script. "
            f"Episode kind: {episode_kind}.\n\n"
            f"<blog>\n{source_text}\n</blog>"
        )

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.anthropic_model,
                "max_tokens": 4096,
                "system": self.system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        text = data["content"][0]["text"]

        chunks = [c.strip() for c in text.split("[CHUNK_BREAK]") if c.strip()]
        return ScriptResult(
            text=text,
            chunks=chunks,
            char_count=len(text),
            metadata={
                "model": settings.anthropic_model,
                "prompt_version": self.prompt_version,
                "usage": data.get("usage", {}),
            },
        )
