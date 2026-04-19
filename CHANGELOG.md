# CHANGELOG

## [0.1.0] — 2026-04-19

Initial commit. End-to-end pipeline working locally.

### Added
- `ClaudeScriptAdapter` — Claude Sonnet 4.6 rewrites blog posts into
  podcast monologue scripts with `[CHUNK_BREAK]` markers
- `ElevenLabsV3TTS` — TTS via ElevenLabs v3 with cloned voice
- `audio.postprocess.concat_mp3` — ffmpeg-based lossless MP3 concat
- Three episodes generated and validated:
  - Ep01: "外科醫師為什麼該學寫程式" — 7:50
  - Ep02: "Python,猶豫中的醫師同事版" — 9:00
  - Ep03: "你的 Python 第一週 onboarding" — 10:12
- Three versioned prompt templates:
  - `v1_generic` (manifesto-style adaptation)
  - `v1_persuasion` (convincing a hesitant listener)
  - `v1_onboarding` (prescriptive first-day guide)
- Show brand metadata — show name: 腸所欲言 (ColonClub)
- Design docs, known limitations, voice tuning notes

### Known limitations
- ElevenLabs v3 does not support `previous_request_ids`
  (cross-chunk prosody chaining). Chunks generated independently.
- No intro/outro splicing yet.
- No LUFS normalization yet.
- No Cloudflare R2 upload yet.
- No WordPress webhook trigger yet.
- No RSS feed generation yet.

### Roadmap
- [ ] Improve script adapter for more natural, "spoken-feeling" Chinese
- [ ] Intro/outro splice + LUFS normalization to -16 LUFS
- [ ] R2 upload + public URL generation
- [ ] iTunes-spec-compliant RSS feed builder
- [ ] WordPress mu-plugin to fire webhooks on publish
- [ ] FastAPI webhook receiver
- [ ] Consider hybrid production: AI-narrated for news/tech episodes,
      human-recorded for interviews and emotional episodes
