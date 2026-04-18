"""Configuration management for Auto_Podcast_CRS."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration loaded from environment variables."""

    # OpenAI
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")

    # Models
    SCRIPT_MODEL: str = os.environ.get("SCRIPT_MODEL", "gpt-4o")
    TTS_MODEL: str = os.environ.get("TTS_MODEL", "tts-1")

    # Voices (one per speaker role)
    HOST_VOICE: str = os.environ.get("HOST_VOICE", "alloy")
    GUEST_VOICE: str = os.environ.get("GUEST_VOICE", "nova")

    # Output
    OUTPUT_DIR: Path = Path(os.environ.get("OUTPUT_DIR", "output"))

    @classmethod
    def validate(cls) -> None:
        """Raise ValueError if required settings are missing."""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Copy .env.example to .env and fill in your API key."
            )
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
