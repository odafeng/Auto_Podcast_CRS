"""ElevenLabs v3 implementation of TTSProvider.

Known limitation: v3 does NOT support previous_request_ids for prosody chaining
(API returns HTTP 400). Each chunk is generated independently. See
docs/known_limitations.md for details.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from auto_podcast_crs._http import post_with_retry
from auto_podcast_crs.config import get_settings
from auto_podcast_crs.tts import TTSProvider, TTSResult

log = logging.getLogger(__name__)

V3_CHUNK_CHAR_CAP = 3000


class ElevenLabsV3TTS(TTSProvider):
    BASE_URL = "https://api.elevenlabs.io"

    def __init__(
        self,
        voice_id: str | None = None,
        model_id: str | None = None,
        output_format: str | None = None,
    ):
        s = get_settings()
        self.voice_id = voice_id or s.eleven_voice_id
        self.model_id = model_id or s.eleven_model_id
        self.output_format = output_format or s.eleven_output_format
        if not s.eleven_api_key:
            raise RuntimeError("ELEVEN_API_KEY not set in environment")
        if not self.voice_id:
            raise RuntimeError("ELEVEN_VOICE_ID not set")

    def synthesize(self, chunks: list[str], output_dir: Path) -> TTSResult:
        if not chunks:
            raise ValueError("synthesize called with empty chunks list")

        s = get_settings()
        output_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        total_chars = 0
        timings: list[float] = []

        url = (
            f"{self.BASE_URL}/v1/text-to-speech/{self.voice_id}"
            f"?output_format={self.output_format}"
        )
        headers = {
            "xi-api-key": s.eleven_api_key,
            "Content-Type": "application/json",
        }

        for i, text in enumerate(chunks):
            if len(text) > V3_CHUNK_CHAR_CAP:
                log.warning(
                    "Chunk %d is %d chars — exceeds v3 cap (%d). Expect truncation.",
                    i, len(text), V3_CHUNK_CHAR_CAP,
                )
            total_chars += len(text)
            log.info("TTS chunk %d: %d chars", i, len(text))

            t0 = time.time()
            response = post_with_retry(
                url,
                json={"text": text, "model_id": self.model_id},
                headers=headers,
                timeout=240,
            )
            dt = time.time() - t0
            timings.append(dt)

            out_path = output_dir / f"chunk_{i:02d}.mp3"
            out_path.write_bytes(response.content)
            paths.append(out_path)
            log.info(
                "  chunk %d done: %.1fs, %.0fKB",
                i, dt, len(response.content) / 1024,
            )

        return TTSResult(
            chunk_paths=paths,
            total_chars=total_chars,
            provider="elevenlabs_v3",
            metadata={
                "voice_id": self.voice_id,
                "model_id": self.model_id,
                "output_format": self.output_format,
                "chunk_timings_s": timings,
            },
        )
