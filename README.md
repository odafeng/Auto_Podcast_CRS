# Auto_Podcast_CRS

A podcast production pipeline that turns a blog post into a published
podcast episode — using Claude for script adaptation, ElevenLabs v3 for
voice cloning, ffmpeg for audio finishing, and Cloudflare R2 for hosting.

Built as the infrastructure behind **腸所欲言 (ColonClub)**, a Chinese-
language podcast for colorectal surgery professionals.

---

## Status

🚧 **Beta.** Manual trigger, automatic pipeline.

What works today:
- Blog post markdown → Claude-generated podcast script (v1 + v2 prompts)
- Script → ElevenLabs v3 MP3 chunks → concatenated raw MP3
- Raw MP3 → intro/outro splice + LUFS -16 normalization → finished MP3
- Finished MP3 → Cloudflare R2 upload → public URL
- All episodes' metadata → iTunes-spec RSS feed → R2 upload

What's not yet automated:
- WordPress webhook trigger (you still manually copy blog → `source.md`)
- Submitting the feed to Apple Podcasts Connect and Spotify for Creators
  (one-time setup per platform, not worth automating)

---

## Architecture

```
  WordPress blog post (copy body to episodes/<id>/source.md)
        │
        ▼
┌──────────────────────────────────────────────────┐
│ ScriptAdapter (Claude Sonnet 4.6)                │  scripts/generate_script.py
│   blog → podcast monologue + [CHUNK_BREAK]       │
└──────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────┐
│ TTSProvider (ElevenLabs v3)                      │  scripts/run_tts.py
│   chunks → per-chunk MP3 → concat → raw MP3      │
└──────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────┐
│ AudioFinishing (ffmpeg)                          │  scripts/publish.py
│   raw MP3 → intro/outro splice → -16 LUFS        │    step 1
│                                                  │
│ StorageProvider (Cloudflare R2)                  │    step 2
│   finished MP3 → public URL                      │
│                                                  │
│ RSSFeedBuilder (feedgen)                         │    step 3
│   episodes/*/metadata.yaml → iTunes RSS XML      │
│                                                  │
│ StorageProvider → feed.xml                       │    step 4
└──────────────────────────────────────────────────┘
        │
        ▼
  Apple Podcasts / Spotify (polls the feed URL)
```

---

## Getting started

### Prerequisites

- Python 3.11+
- ffmpeg in your PATH
- An Anthropic API key
- An ElevenLabs API key + a cloned voice ID
- A Cloudflare R2 bucket with public access enabled

### Install

```bash
git clone git@github.com:odafeng/Auto_Podcast_CRS.git
cd Auto_Podcast_CRS

# Core only
pip install -e .

# Full publish pipeline (adds boto3 + feedgen)
pip install -e '.[publish]'

# Dev (adds ruff + pytest + pre-commit)
pip install -e '.[dev,publish]'
```

### Configure

```bash
cp .env.example .env
# Edit .env: ANTHROPIC_API_KEY, ELEVEN_API_KEY, ELEVEN_VOICE_ID,
#           R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
#           R2_PUBLIC_URL, R2_BUCKET
```

### Produce one episode

Two modes, pick the one that fits:

**A. Blog → podcast** (you already wrote the blog post):
```bash
mkdir -p episodes/04_my-slug
cp /path/to/blog.md episodes/04_my-slug/source.md

python scripts/generate_script.py --episode 04_my-slug
python scripts/run_tts.py --episode 04_my-slug
python scripts/publish.py --episode 04_my-slug \
    --intro static/intro.mp3 --outro static/outro.mp3
```

**B. Topic + resources → podcast** (you have a topic in mind and some
reference material):
```bash
mkdir -p episodes/04_my-slug/resources
# drop 2-5 relevant .md files (papers, notes, guidelines) into resources/
# see docs/resource_preparation.md for what belongs there

python scripts/generate_from_topic.py --episode 04_my-slug \
    --topic "your episode topic in one sentence"
python scripts/run_tts.py --episode 04_my-slug
python scripts/publish.py --episode 04_my-slug \
    --intro static/intro.mp3 --outro static/outro.mp3
```

Total time either way: ~3 minutes of pipeline execution. Total cost:
~$0.50 per episode.

---

## Environment variables

All credentials live in `.env` (git-ignored). See `.env.example` for the
template.

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude for script rewriting |
| `ANTHROPIC_MODEL` | Model string (default `claude-sonnet-4-6`) |
| `ANTHROPIC_MAX_TOKENS` | Output cap (default 8000) |
| `ELEVEN_API_KEY` | ElevenLabs TTS |
| `ELEVEN_VOICE_ID` | Your cloned voice ID |
| `R2_ENDPOINT` | R2 S3-compatible write endpoint |
| `R2_ACCESS_KEY_ID` | R2 access key |
| `R2_SECRET_ACCESS_KEY` | R2 secret |
| `R2_PUBLIC_URL` | R2 public read URL (for RSS `<enclosure>`) |
| `R2_BUCKET` | R2 bucket name |
| `INTRO_MP3_PATH` | (Optional) intro audio; CLI flag `--intro` overrides |
| `OUTRO_MP3_PATH` | (Optional) outro audio; CLI flag `--outro` overrides |
| `AUTOPODCAST_LOG_LEVEL` | DEBUG/INFO/WARNING/ERROR |

---

## Design principles

1. **Modular providers** — each layer (script, TTS, storage, RSS) sits
   behind an interface so providers can be swapped without touching
   orchestration. ElevenLabs → Azure TTS is a one-file change.
2. **Per-episode reproducibility** — every episode has its own folder
   with the exact prompt version, source material, generated script,
   and metadata. Rerunning a six-month-old episode produces byte-
   identical script.
3. **Prompts are versioned files** — system prompts live in
   `auto_podcast_crs/scripts/prompts/*.md`. Iterating means a new
   version (`v3_*`), not mutating v2.
4. **Known limitations are documented** — see `docs/known_limitations.md`.
5. **Fail fast on caller bugs, lazy on external deps** — input validation
   runs before any ffmpeg/boto3/API checks, so a missing `intro.mp3` or
   an empty chunk list surfaces a clear error immediately.

---

## Tests & CI

```bash
pytest -v                        # 55 tests, ~25s
ruff check .                     # lint
pre-commit run --all-files       # format + private-key detection
```

CI runs ruff + pytest on every push to `main` via GitHub Actions.

---

## License

TBD — currently private. Will likely be MIT if/when made public.

## Author

黃士峯 Shih-Feng Huang, MD
Colorectal Surgery, Kaohsiung Veterans General Hospital
GitHub: [@odafeng](https://github.com/odafeng)
