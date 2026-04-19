"""ScriptAdapter interface — blog → podcast monologue script."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ScriptResult:
    text: str
    chunks: list[str]  # split by [CHUNK_BREAK]
    char_count: int
    metadata: dict  # usage stats, model id, prompt version


class ScriptAdapter(ABC):
    """Turns a blog post into a TTS-ready podcast monologue script."""

    @abstractmethod
    def adapt(
        self,
        source_text: str,
        episode_kind: str,  # "manifesto" | "persuasion" | "onboarding" | "generic"
    ) -> ScriptResult:
        """Rewrite source_text into a podcast script with [CHUNK_BREAK] markers."""
        ...
