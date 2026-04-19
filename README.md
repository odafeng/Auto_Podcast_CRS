# Auto_Podcast_CRS

An end-to-end automated podcast pipeline that turns a WordPress blog post into a
published podcast episode — using Claude Sonnet for script adaptation,
ElevenLabs v3 for voice cloning, and (eventually) Cloudflare R2 for hosting.

Built as the infrastructure behind **腸所欲言 (ColonClub)**, a Chinese-language
podcast for colorectal surgery professionals.

---

## Status

🚧 Alpha. Three episodes shipped as local MP3 files.
R2 hosting integration and WordPress webhook not yet wired up.

---

## Architecture

```
WordPress publish
      │ webhook (not yet implemented)
      ▼
┌─────────────────────────────────────────────────┐
│  FastAPI /webhook/wordpress (future)            │
└─────────────────────────────────────────────────┘
      │
      ├─► 1. WordPressSource   (wp-json/wp/v2/posts/{id})
      │
      ├─► 2. ScriptAdapter     (Claude Sonnet 4.6)
      │         └─► blog → podcast monologue + v3 audio tags
      │         └─► splits into chunks with [CHUNK_BREAK]
      │
      ├─► 3. ElevenLabsV3TTS   (cloned voice)
      │         └─► one POST per chunk, MP3 out
      │
      ├─► 4. AudioPostProcessor (ffmpeg)
      │         └─► concat chunks → intro → outro → LUFS norm
      │
      ├─► 5. R2Storage + RSSFeedBuilder (not yet implemented)
      │         ├─► audio PUT to Cloudflare R2
      │         └─► update feed.xml (iTunes-spec)
      │
      └─► 6. Notification (future)
```

---

## What's in this repo right now

- `auto_podcast_crs/scripts/` — script adaptation layer (Claude-powered)
- `auto_podcast_crs/tts/` — TTS layer (ElevenLabs v3)
- `auto_podcast_crs/audio/` — ffmpeg post-processing
- `scripts/` — CLI entry points you can run today
- `episodes/` — source material + generated scripts + metadata for each episode
- `brand/` — show identity, taglines, description templates
- `docs/` — design notes, known API limitations, voice tuning notes

---

## Getting started

### Prerequisites

- Python 3.11+
- ffmpeg in your PATH
- An ElevenLabs API key + a voice ID
- An Anthropic API key

### Setup

```bash
# 1. Clone
git clone git@github.com:odafeng/Auto_Podcast_CRS.git
cd Auto_Podcast_CRS

# 2. Install dependencies (uv is recommended, pip works too)
uv sync
# or: pip install -e .

# 3. Copy env template and fill in your keys
cp .env.example .env
# Edit .env with your real keys

# 4. Generate a script from a blog post
python scripts/generate_script.py \
  --episode 04 \
  --blog-path episodes/04_new-episode/source.md

# 5. Run TTS on the generated script
python scripts/run_tts.py --episode 04
```

---

## Environment variables

All credentials live in `.env` (git-ignored). See `.env.example` for the template.

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude Sonnet 4.6 for script rewriting |
| `ELEVEN_API_KEY` | ElevenLabs TTS |
| `ELEVEN_VOICE_ID` | Your cloned voice ID |
| `R2_ENDPOINT` | Cloudflare R2 S3-compatible endpoint (future) |
| `R2_ACCESS_KEY_ID` | R2 access key (future) |
| `R2_SECRET_ACCESS_KEY` | R2 secret (future) |
| `R2_PUBLIC_URL` | Public read URL for R2 bucket (future) |

---

## Design principles

1. **Modular providers** — each layer (source, script, TTS, storage) is behind
   an interface, so providers can be swapped without touching orchestration.
2. **Per-episode reproducibility** — every episode has its own folder with the
   exact prompt version, source material, and generated script. You can rerun
   a six-month-old episode and get byte-identical output.
3. **Prompts are versioned files** — system prompts live in
   `auto_podcast_crs/scripts/prompts/*.md`. When we iterate, we create a new
   version, not mutate the old one.
4. **Known limitations are documented** — when we hit an API quirk (like
   ElevenLabs v3 not supporting `previous_request_ids`), it goes into
   `docs/known_limitations.md` so we don't re-step on it later.

---

## License

TBD — currently private. Will likely be MIT if/when made public.

## Author

黃士峯 Shih-Feng Huang, MD
Colorectal Surgery, Kaohsiung Veterans General Hospital
GitHub: [@odafeng](https://github.com/odafeng)
