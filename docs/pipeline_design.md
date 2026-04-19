# Pipeline Design

## Goal

Turn a published WordPress blog post into a published podcast episode
with minimal human intervention — ideally, zero clicks between "hit
Publish on WP" and "episode is live on Apple Podcasts".

## Current state (v0.4.0 beta)

```
Manual:  blog post URL → [me] → saved as source.md
   |
   ├── ScriptAdapter (Claude)      ← works, v2 default
   ├── TTSProvider (ElevenLabs v3) ← works, retry + logging
   ├── AudioPostProcessor (ffmpeg) ← works, concat only
   ├── AudioFinishing (ffmpeg)     ← works, intro/outro + LUFS -16
   ├── StorageProvider (R2)        ← works, boto3 via S3-compat API
   ├── RSSFeedBuilder (feedgen)    ← works, iTunes-spec
   ├── publish.py orchestrator     ← works, single command
   └── WordPress webhook trigger   ← not yet wired
```

## Target state (v1)

```
Automatic: WP publish → webhook → pipeline → R2 → RSS → Apple/Spotify poll
```

## Module boundaries

The goal is to be able to swap any one of these without touching the others:

### SourceAdapter
- Input: an identifier (WP post ID, URL, or local file path)
- Output: plain text + metadata (title, featured image, published date)
- Implementations:
  - `WordPressSource` — via wp-json REST API (TODO)
  - `LocalMarkdownSource` — for prompt-driven episodes (TODO)

### ScriptAdapter
- Input: plain text + episode kind
- Output: podcast monologue script with [CHUNK_BREAK] markers
- Implementations:
  - `ClaudeScriptAdapter` ✅ (current)
- Prompts are versioned files under `scripts/prompts/`

### TTSProvider
- Input: list of chunks
- Output: list of MP3 paths + metadata
- Implementations:
  - `ElevenLabsV3TTS` ✅ (current)
  - `ElevenLabsMultilingualV2TTS` (fallback for chaining, TODO)

### AudioPostProcessor
- Input: list of MP3 paths + optional intro/outro
- Output: single final MP3 at target LUFS
- Current: concat only. TODO: intro/outro splicing, LUFS normalization

### StorageProvider
- Input: local MP3 path + object key
- Output: public URL
- Implementations:
  - `R2Storage` ✅ (current) — boto3 + Cloudflare R2

### AudioFinishing
- Input: raw MP3 + optional intro/outro
- Output: single normalized MP3 at target LUFS
- `splice_intro_outro()` handles optional intro/outro gracefully
- `normalize_lufs()` targets -16 LUFS via ffmpeg loudnorm

### RSSFeedBuilder
- Input: list of episode metadata
- Output: iTunes-spec-compliant RSS XML
- Target spec: https://help.apple.com/itc/podcasts_connect/#/itcb54353390

## Why this modular structure

Because every dependency in this pipeline is a different API with its
own quirks and pricing, we need to be able to swap any one out. Known
failure modes:
- ElevenLabs changes pricing → swap for Azure Neural or OpenAI TTS
- Claude rate-limits during peak → swap for a local LLM for rewrite
- R2 has an outage → swap to S3 or B2
- WordPress API breaks → swap to RSS polling

None of these swaps should require rewriting the pipeline — only the
relevant adapter.

## What is NOT modular (by design)

- **Episode folder structure** (`episodes/<id>/{source, script, metadata}`)
  — this is the canonical format. Changing it invalidates old episodes.
- **Audio tag vocabulary** (`[pauses]`, `[emphasizes]`, etc.) — tied to
  ElevenLabs v3. If we switch TTS, we need a tag translation layer.
- **Show brand metadata** — `brand/metadata.md` is the source of truth
  for RSS feed fields.

## Non-goals

Explicitly NOT trying to do:
- Real-time TTS (we're batch)
- Multiple languages per episode (one language per episode)
- Video podcasts (audio only)
- Multi-host / dialogue (monologue only for now; dialogue is v2)
- Live streaming (prerecorded only)
