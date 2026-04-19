"""Centralized configuration — loads from environment variables.

Usage:
    from auto_podcast_crs.config import settings
    api_key = settings.anthropic_api_key
"""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


class Settings(BaseModel):
    # Anthropic
    anthropic_api_key: str = Field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = Field(default="claude-sonnet-4-6")

    # ElevenLabs
    eleven_api_key: str = Field(default_factory=lambda: os.environ.get("ELEVEN_API_KEY", ""))
    eleven_voice_id: str = Field(default_factory=lambda: os.environ.get("ELEVEN_VOICE_ID", ""))
    eleven_model_id: str = Field(
        default_factory=lambda: os.environ.get("ELEVEN_MODEL_ID", "eleven_v3")
    )
    eleven_output_format: str = Field(
        default_factory=lambda: os.environ.get("ELEVEN_OUTPUT_FORMAT", "mp3_44100_128")
    )

    # Cloudflare R2 (optional, for future use)
    r2_endpoint: str = Field(default_factory=lambda: os.environ.get("R2_ENDPOINT", ""))
    r2_access_key_id: str = Field(
        default_factory=lambda: os.environ.get("R2_ACCESS_KEY_ID", "")
    )
    r2_secret_access_key: str = Field(
        default_factory=lambda: os.environ.get("R2_SECRET_ACCESS_KEY", "")
    )
    r2_public_url: str = Field(default_factory=lambda: os.environ.get("R2_PUBLIC_URL", ""))
    r2_bucket: str = Field(default_factory=lambda: os.environ.get("R2_BUCKET", "autopodcast"))

    # Paths
    repo_root: Path = REPO_ROOT
    episodes_dir: Path = REPO_ROOT / "episodes"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
