"""ElevenLabs v3 implementation of TTSProvider.

Known limitation: v3 does NOT support previous_request_ids for prosody chaining
(API returns HTTP 400). Each chunk is generated independently. See
docs/known_limitations.md for details.
"""
import time
from pathlib import Path

import requests

from auto_podcast_crs.config import settings
from auto_podcast_crs.tts import TTSProvider, TTSResult


class ElevenLabsV3TTS(TTSProvider):
    BASE_URL = "https://api.elevenlabs.io"

    def __init__(
        self,
        voice_id: str | None = None,
        model_id: str | None = None,
        output_format: str | None = None,
    ):
        self.voice_id = voice_id or settings.eleven_voice_id
        self.model_id = model_id or settings.eleven_model_id
        self.output_format = output_format or settings.eleven_output_format
        if not settings.eleven_api_key:
            raise RuntimeError("ELEVEN_API_KEY not set in environment")

    def synthesize(self, chunks: list[str], output_dir: Path) -> TTSResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        total_chars = 0
        timings: list[float] = []

        url = (
            f"{self.BASE_URL}/v1/text-to-speech/{self.voice_id}"
            f"?output_format={self.output_format}"
        )
        headers = {
            "xi-api-key": settings.eleven_api_key,
            "Content-Type": "application/json",
        }

        for i, text in enumerate(chunks):
            total_chars += len(text)
            t0 = time.time()
            response = requests.post(
                url,
                json={"text": text, "model_id": self.model_id},
                headers=headers,
                timeout=240,
            )
            response.raise_for_status()
            dt = time.time() - t0
            timings.append(dt)

            out_path = output_dir / f"chunk_{i:02d}.mp3"
            out_path.write_bytes(response.content)
            paths.append(out_path)
            print(f"  chunk {i}: {len(text)} chars → {dt:.1f}s, {len(response.content)/1024:.0f}KB")

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
