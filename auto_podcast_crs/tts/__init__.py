"""TTSProvider interface — script text → MP3 audio."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TTSResult:
    chunk_paths: list[Path]
    total_chars: int
    provider: str
    metadata: dict


class TTSProvider(ABC):
    """Generates audio from script text."""

    @abstractmethod
    def synthesize(
        self,
        chunks: list[str],
        output_dir: Path,
    ) -> TTSResult:
        """Generate one audio file per chunk. Caller handles concat."""
        ...
