"""Tests for src.config."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import Config


class TestConfig:
    def test_defaults(self):
        with patch.dict(os.environ, {}, clear=False):
            assert Config.SCRIPT_MODEL in ("gpt-4o", os.environ.get("SCRIPT_MODEL", "gpt-4o"))
            assert Config.TTS_MODEL in ("tts-1", os.environ.get("TTS_MODEL", "tts-1"))

    def test_validate_raises_without_api_key(self):
        with patch.object(Config, "OPENAI_API_KEY", ""):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                Config.validate()

    def test_validate_creates_output_dir(self, tmp_path):
        new_dir = tmp_path / "podcast_out"
        with patch.object(Config, "OPENAI_API_KEY", "sk-test"), \
             patch.object(Config, "OUTPUT_DIR", new_dir):
            Config.validate()
            assert new_dir.is_dir()

    def test_output_dir_type(self):
        assert isinstance(Config.OUTPUT_DIR, Path)
