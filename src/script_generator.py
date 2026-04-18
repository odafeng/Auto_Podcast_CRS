"""Script generation module – creates a structured podcast script using an LLM."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import List

from openai import OpenAI

from .config import Config

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a professional podcast scriptwriter. Given a topic, produce an engaging,
conversational podcast script between a Host and a Guest.

Return ONLY valid JSON with the following structure (no markdown fences):
{
  "title": "<podcast episode title>",
  "description": "<one-sentence episode description>",
  "segments": [
    {"speaker": "Host",  "text": "..."},
    {"speaker": "Guest", "text": "..."}
  ]
}

Rules:
- Alternate between Host and Guest naturally.
- Include an introduction, 3–5 discussion segments, and a closing.
- Keep each turn between 2 and 6 sentences.
- Do NOT include any text outside the JSON object.
"""


@dataclass
class ScriptSegment:
    """A single spoken turn in the podcast script."""

    speaker: str
    text: str


@dataclass
class PodcastScript:
    """Full podcast script produced by the LLM."""

    title: str
    description: str
    segments: List[ScriptSegment] = field(default_factory=list)


class ScriptGenerator:
    """Generates a podcast script for a given topic using OpenAI chat completions."""

    def __init__(self, config: Config | None = None) -> None:
        self._config = config or Config()
        self._client = OpenAI(api_key=self._config.OPENAI_API_KEY)

    def generate(self, topic: str) -> PodcastScript:
        """Return a :class:`PodcastScript` for *topic*.

        Parameters
        ----------
        topic:
            The subject or title of the podcast episode.

        Returns
        -------
        PodcastScript
            Structured script ready for TTS conversion.
        """
        logger.info("Generating script for topic: %s", topic)
        response = self._client.chat.completions.create(
            model=self._config.SCRIPT_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Topic: {topic}"},
            ],
            temperature=0.8,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        logger.debug("Raw LLM response: %s", raw)
        return self._parse(raw)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse(raw: str) -> PodcastScript:
        """Parse the raw JSON string returned by the LLM."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON: {exc}\n\nRaw output:\n{raw}") from exc

        segments = [
            ScriptSegment(speaker=seg["speaker"], text=seg["text"])
            for seg in data.get("segments", [])
        ]
        return PodcastScript(
            title=data.get("title", "Untitled Episode"),
            description=data.get("description", ""),
            segments=segments,
        )
