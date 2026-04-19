# CHANGELOG

## [0.3.0] — 2026-04-19

Script quality pass. The v1 prompts produced scripts that read well but
sounded like someone narrating copy — grammatically clean, listicle-
structured, emotionally flat. v2 forces conversational register.

### Added
- `system_v2_generic.md`, `system_v2_persuasion.md`, `system_v2_onboarding.md`
  — new conversational prompts. Key differences from v1:
  - Explicitly forbids listicle structure ("第一⋯第二⋯第三⋯")
  - Requires filler/hedge words ("欸", "然後呢", "對啊", "怎麼講")
  - Requires direct listener address ("你想想看" / "你有沒有遇過")
  - Restricts audio tags — bans `[excited]`, `[whispers]`, `[shouts]`;
    uses `[pauses]` for thinking, not just drama
  - Each prompt carries before/after examples showing the v1→v2 transform
- `docs/prompt_ab_testing.md` — blind-listening protocol for comparing
  prompt versions before promoting a new default.
- `tests/test_v2_prompts.py` — guardrail tests that future edits don't
  quietly undo the v2 invariants (no listicle, has fillers, direct
  address, no overacting tags).
- CLI `--prompt-version` accepts all six versions; default is now
  `v2_generic`.

### Changed
- `docs/workflow.md` updated: v2 is the current default, v1 retained
  as legacy/baseline.
- v1 prompts explicitly NOT deleted — they're the reproducibility
  record for ep01–03, and the A/B baseline going forward.

### Not yet done
- Actual A/B comparison (regenerate ep01–03 with v2, listen blind,
  score). Protocol is documented; execution is the author's call.
- Conversational-style prompt for future episode types (interview,
  news-digest, Q&A) — build when needed.

---

## [0.2.0] — 2026-04-19

Production-hardening pass. Same pipeline, less fragility.

### Added
- `auto_podcast_crs._http.post_with_retry` — exponential backoff on
  5xx / 429 / network errors. 4xx surfaces immediately (no silent retry
  on request-side bugs). Built on `tenacity`.
- `auto_podcast_crs._logging.setup_logging` — centralized logging
  setup. Level controlled by `--log-level` CLI flag or
  `AUTOPODCAST_LOG_LEVEL` env var.
- `ANTHROPIC_MAX_TOKENS` env var — output cap is no longer hardcoded
  at 4096.
- `ANTHROPIC_MODEL` env var — model string is now config-driven for
  A/B testing (Sonnet 4.6 vs Opus 4.7, etc.).
- `split_chunks()` as a standalone, testable function.
- Input validation: empty chunk lists, missing files, missing binaries
  (ffmpeg/ffprobe) now raise clear errors instead of crashing downstream.
- Tests:
  - `tests/test_chunk_split.py` — 7 cases covering the core text-splitting
    invariant (the one thing that, if broken, silently corrupts every
    episode).
  - `tests/test_prompt_loader.py` — validates all shipped prompts load
    and overrides work.
  - `tests/test_http_retry.py` — verifies retry-on-5xx, no-retry-on-400,
    and give-up-after-N behavior. Stubs `requests.post`, no network.
  - `tests/test_audio.py` — guard-rail tests for `concat_mp3` (empty
    input, missing files).
- GitHub Actions CI: ruff + pytest on every push/PR to `main`.
- `.pre-commit-config.yaml`: ruff, trailing whitespace, large-file guard,
  private-key detector.

### Changed
- All `print()` calls replaced with module-level loggers. Log format:
  `HH:MM:SS | LEVEL | module | message`.
- `ClaudeScriptAdapter` and `ElevenLabsV3TTS` now route through
  `post_with_retry`. Both fail fast on bad credentials before the first
  network call.
- `concat_mp3` now checks ffmpeg presence and validates all chunk
  files exist before spawning the subprocess.

### Not yet done (roadmap, unchanged)
- [ ] R2 upload + public URL generation
- [ ] iTunes-spec RSS feed builder
- [ ] WordPress webhook receiver
- [ ] Intro/outro splicing + LUFS normalization
- [ ] Unified CLI entry point (`python -m auto_podcast_crs ...`)
- [ ] Swap `requests` → official `anthropic` SDK (gains: streaming,
  built-in retry, prompt caching)

---

## [0.1.0] — 2026-04-19

Initial commit. End-to-end pipeline working locally.

### Added
- `ClaudeScriptAdapter` — Claude Sonnet 4.6 rewrites blog posts into
  podcast monologue scripts with `[CHUNK_BREAK]` markers.
- `ElevenLabsV3TTS` — TTS via ElevenLabs v3 with cloned voice.
- `audio.postprocess.concat_mp3` — ffmpeg-based lossless MP3 concat.
- Three episodes generated and validated:
  - Ep01: "外科醫師為什麼該學寫程式" — 7:50
  - Ep02: "Python,猶豫中的醫師同事版" — 9:00
  - Ep03: "你的 Python 第一週 onboarding" — 10:12
- Three versioned prompt templates:
  - `v1_generic` (manifesto-style adaptation)
  - `v1_persuasion` (convincing a hesitant listener)
  - `v1_onboarding` (prescriptive first-day guide)
- Show brand metadata — show name: 腸所欲言 (ColonClub).
- Design docs, known limitations, voice tuning notes.

### Known limitations
- ElevenLabs v3 does not support `previous_request_ids` (cross-chunk
  prosody chaining). Chunks generated independently.
- No intro/outro splicing yet.
- No LUFS normalization yet.
- No Cloudflare R2 upload yet.
- No WordPress webhook trigger yet.
- No RSS feed generation yet.
