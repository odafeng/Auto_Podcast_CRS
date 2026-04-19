# CHANGELOG

## [0.5.0] — 2026-04-19

Topic-based episode generation. Two pipelines now coexist: the original
blog→script flow (v2 default) and a new topic+resources→script flow (v3).

### Added
- `auto_podcast_crs/scripts/resources.py` — per-episode resource loader.
  Reads `episodes/<id>/resources/*.md` (or `.markdown`/`.txt`), sorts
  stably by filename for reproducibility, formats as XML-tagged blocks
  for Claude, enforces a conservative token budget (400k estimated
  tokens, ~half of Sonnet 4.6's context).
- `auto_podcast_crs/scripts/topic_to_script.py` — `TopicScriptAdapter`
  class. Takes a topic string + a resource bundle + optional angle,
  returns a full `TopicScriptResult` with script text, chunks,
  resources used, and usage metadata. Includes a verbatim-copy
  detector that warns when the model reproduces 40+ char runs from
  any source file (the v3 prompt explicitly forbids this; the warning
  is the safety net).
- `auto_podcast_crs/scripts/prompts/system_v3_topic_generic.md` — new
  v3 prompt. Inherits the v2 conversational-style rules (no listicle,
  required fillers, direct address, no overacting tags) and adds
  synthesis-specific guidance: how to handle source attribution (口語
  format: "2024 年有篇 Annals of Surgery 的研究…"), how to avoid
  paper-abstract register, how to weave author perspective with data,
  how to handle conflicting sources.
- `scripts/generate_from_topic.py` — new CLI for topic mode. Requires
  `--episode` and `--topic`, accepts optional `--angle` and
  `--resources-dir` overrides. Writes `script.txt`, `sources_used.yaml`
  (audit trail: filenames + char counts + timestamp), and updates
  `metadata.yaml` (creates if absent).
- `docs/resource_preparation.md` — curation guide: what belongs in
  resources/, what doesn't, naming conventions, how many files.
- Tests: +17 covering resource loading (file discovery, ordering,
  extension filtering, token budget enforcement, XML formatting) and
  topic script generation (prompt construction, resource inclusion,
  angle handling, empty-topic rejection, verbatim-copy detection).

### Changed
- `docs/workflow.md` now documents both modes (Option A: blog,
  Option B: topic+resources).
- `README.md` "Produce one episode" section has two sub-sections for
  the two modes.
- `metadata.yaml` schema now supports `source.type:
  "topic_plus_resources"` alongside the existing
  `source.type: "wordpress_post"`.
- `pyproject.toml` version → 0.5.0.

### Not changed
- v1/v2 prompts and `generate_script.py` retained unchanged — the
  blog→script flow continues to work. Both flows converge on the same
  `script.txt`, so downstream `run_tts.py` / `publish.py` don't know
  or care which one produced it.

### Design choices worth documenting
- **Per-episode `resources/` folder, not global.** `episodes/<id>/resources/`
  means each episode's bibliography is git-tracked next to its script —
  trivial reproducibility in six months. A global `resources/` would
  leak context across episodes and lose that trail.
- **`TopicScriptAdapter` is not a subclass of `ScriptAdapter`.** The
  inputs are fundamentally different (one source_text vs topic + N
  documents + optional angle), so forcing them into one ABC would be
  false unification. They share the same output type downstream
  (`script.txt`), which is the only integration point that matters.
- **Verbatim-copy detection is a warning, not an error.** The v3
  prompt forbids it; if Claude violates, we want visibility, not
  a hard stop (sometimes the "copy" is a technical term that can't
  be rephrased).

---

## [0.4.0] — 2026-04-19

End-to-end publishing. The pipeline now genuinely goes from `source.md`
to "live on Apple Podcasts" without manual intervention except the
one-time feed submission to Apple/Spotify.

### Added
- `auto_podcast_crs/audio/finishing.py`:
  - `splice_intro_outro()` — concat intro + main + outro, gracefully
    degrades if either optional file is absent
  - `normalize_lufs()` — ffmpeg `loudnorm` filter targeting -16 LUFS
    (Apple/Spotify program loudness spec)
  - `finish_episode()` — splice + normalize in one call, with temp
    file cleanup
- `auto_podcast_crs/storage/`:
  - `StorageProvider` ABC — upload + exists
  - `R2Storage` — boto3-based Cloudflare R2 implementation, fails fast
    on missing creds, mime-type guessing, public URL composition
- `auto_podcast_crs/rss/`:
  - `ShowMetadata` + `EpisodeMetadata` dataclasses
  - `build_rss_feed()` — feedgen-based iTunes-spec RSS generator
    (handles `<itunes:category>`, `<itunes:explicit>`, `<enclosure>`,
    UTC normalization, newest-first ordering)
- `auto_podcast_crs/pipeline.py` + `scripts/publish.py` — orchestrator
  that runs: finish → upload MP3 → scan all published episodes →
  rebuild feed.xml → upload feed
- Tests: +20 covering audio finishing (real ffmpeg smoke tests with
  sine-tone inputs), R2 (mocked boto3), RSS (feedgen output validation,
  ordering, namespace compliance)
- New CLI flags: `--intro`, `--outro`, `--target-lufs` on `publish.py`;
  falls back to `INTRO_MP3_PATH` / `OUTRO_MP3_PATH` env vars

### Changed
- `pyproject.toml` version → 0.4.0
- New optional extras: `storage` (boto3), `rss` (feedgen), `publish`
  (both). Install with `pip install -e '.[publish]'` for the full
  pipeline.
- README: removed the "end-to-end" oversell that was accurate in
  aspiration but not in code. New status section is precise about what
  works and what doesn't.
- `.env.example` updated with R2 + intro/outro env vars.

### Fixed
- `audio.postprocess.concat_mp3` and `get_audio_duration` now validate
  inputs BEFORE requiring ffmpeg. Previously, caller bugs (empty list,
  missing file) were masked as "ffmpeg not in PATH" on systems where
  ffmpeg was absent. Regression test added.
- CI workflow now installs ffmpeg (ubuntu-latest runners don't
  pre-install it).

### Not yet done
- WordPress mu-plugin + FastAPI webhook receiver (blog-publish → auto
  trigger publish.py). Currently blog → source.md is manual copy.
- Apple Podcasts / Spotify one-time feed submission (not worth
  automating for a single submission).
- Brand metadata loader that parses `brand/metadata.md` — for now,
  show metadata is hardcoded in `pipeline.load_show_metadata()`.

---

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
  quietly undo the v2 invariants.
- CLI `--prompt-version` accepts all six versions; default is now
  `v2_generic`.

### Changed
- `docs/workflow.md` updated: v2 is the current default, v1 retained
  as legacy/baseline.

---

## [0.2.0] — 2026-04-19

Production-hardening pass. Same pipeline, less fragility.

### Added
- `auto_podcast_crs._http.post_with_retry` — exponential backoff on
  5xx / 429 / network errors.
- `auto_podcast_crs._logging.setup_logging` — centralized logging setup.
- `ANTHROPIC_MAX_TOKENS` / `ANTHROPIC_MODEL` env vars.
- `split_chunks()` as a standalone, testable function.
- Input validation across all modules.
- 20 tests covering split_chunks, prompt loading, retry behavior,
  audio guard rails.
- GitHub Actions CI: ruff + pytest on push/PR to `main`.
- `.pre-commit-config.yaml`.

### Changed
- All `print()` calls replaced with module-level loggers.
- `ClaudeScriptAdapter` and `ElevenLabsV3TTS` route through retry
  wrapper and fail-fast on bad credentials.

---

## [0.1.0] — 2026-04-19

Initial commit. End-to-end pipeline working locally.

### Added
- `ClaudeScriptAdapter` — Claude Sonnet 4.6 rewrites blog posts into
  podcast monologue scripts with `[CHUNK_BREAK]` markers.
- `ElevenLabsV3TTS` — TTS via ElevenLabs v3 with cloned voice.
- `audio.postprocess.concat_mp3` — ffmpeg-based lossless MP3 concat.
- Three episodes generated: Ep01, Ep02, Ep03.
- Three versioned prompt templates.
- Show brand metadata — show name: 腸所欲言 (ColonClub).
- Design docs, known limitations, voice tuning notes.
