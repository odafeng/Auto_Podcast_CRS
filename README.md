# Auto_Podcast_CRS

An end-to-end pipeline that generates a complete AI-powered podcast episode from a single topic.

## Overview

```
Topic ──► Script Generator (LLM) ──► TTS Converter ──► Audio Processor ──► Episode MP3
```

| Step | Module | What it does |
|------|--------|--------------|
| 1 | `src/script_generator.py` | Calls OpenAI GPT to produce a conversational Host/Guest script in JSON |
| 2 | `src/tts_converter.py` | Calls OpenAI TTS to render each script turn as an MP3 segment |
| 3 | `src/audio_processor.py` | Merges segments (with short pauses) into one episode file |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** MP3 output requires [ffmpeg](https://ffmpeg.org/download.html) to be installed on your system.
> WAV output works without ffmpeg.

### 2. Configure your API key

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 3. Generate a podcast

```bash
python pipeline.py "The future of renewable energy"
# or
python pipeline.py --topic "Space exploration in the 21st century"
```

The episode MP3 is saved in the `output/` directory.

## Configuration

All settings can be changed in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `SCRIPT_MODEL` | `gpt-4o` | LLM model for script generation |
| `TTS_MODEL` | `tts-1` | TTS model (`tts-1` or `tts-1-hd`) |
| `HOST_VOICE` | `alloy` | Voice for the Host speaker |
| `GUEST_VOICE` | `nova` | Voice for the Guest speaker |
| `OUTPUT_DIR` | `output` | Directory where audio files are saved |

Available voices: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`.

## Project Structure

```
Auto_Podcast_CRS/
├── pipeline.py              # CLI entry point
├── requirements.txt
├── .env.example
├── src/
│   ├── config.py            # Configuration management
│   ├── script_generator.py  # LLM-based script generation
│   ├── tts_converter.py     # Text-to-speech conversion
│   ├── audio_processor.py   # Audio merging
│   └── pipeline.py          # Orchestrator (PodcastPipeline class)
├── tests/
│   ├── test_config.py
│   ├── test_script_generator.py
│   ├── test_tts_converter.py
│   ├── test_audio_processor.py
│   └── test_pipeline.py
└── output/                  # Generated audio files (git-ignored)
```

## Using the Pipeline Programmatically

```python
from src.pipeline import PodcastPipeline

pipeline = PodcastPipeline()
output_path = pipeline.run("The ethics of artificial intelligence")
print(f"Episode saved to: {output_path}")
```

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## License

MIT
