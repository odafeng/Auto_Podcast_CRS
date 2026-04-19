# Producing a New Episode — Workflow

For future you, after the initial scaffolding is done.

## 1. Create the episode folder

```bash
mkdir -p episodes/04_your-episode-slug
```

Naming: `NN_kebab-case-slug` where NN is zero-padded episode number.

## 2. Put the source material in

### Option A — Blog-based episode (`generate_script.py`)
Copy the blog post body into `source.md`. Adapts one blog post into a
podcast script.

### Option B — Topic-based episode (`generate_from_topic.py`)
Create `episodes/<id>/resources/` and drop 2–5 relevant `.md` files
(papers, notes, guidelines). See `docs/resource_preparation.md` for what
goes there. Synthesizes an original script on the topic from those
sources.

### For a prompt-driven episode (neither source.md nor resources)
Skip both. Write your brief at the bottom of this workflow doc, and
pass it into the Claude API yourself.

## 3. Choose a prompt version

For **Option A** (blog → script, via `generate_script.py`):

| Prompt version | Use when |
|---|---|
| `v2_generic` (**default**) | First-person reflection / manifesto, conversational tone |
| `v2_persuasion` | Convincing someone on the fence, conversational tone |
| `v2_onboarding` | Prescriptive first-day guide, conversational tone |
| `v1_generic` | (legacy) Original manifesto template — cleaner but reads more like copy |
| `v1_persuasion` | (legacy) |
| `v1_onboarding` | (legacy) |

For **Option B** (topic + resources → script, via `generate_from_topic.py`):

| Prompt version | Use when |
|---|---|
| `v3_topic_generic` (**default**) | Topic-based synthesis; you supply 2-5 resource files, Claude writes the script |

v3 includes the v2 conversational-style rules and adds synthesis-specific
guidance (how to handle source attribution, how to avoid paper-abstract
register, how to weave author perspective with data).

## 4. Generate the script

For **Option A**:
```bash
python scripts/generate_script.py \
    --episode 04_your-episode-slug \
    --prompt-version v2_generic \
    --episode-kind manifesto
```

For **Option B**:
```bash
# Make sure episodes/04_your-episode-slug/resources/ has 2-5 .md files first
python scripts/generate_from_topic.py \
    --episode 04_your-episode-slug \
    --topic "your episode topic in one sentence" \
    [--angle "optional extra framing"]
```

Both produce `episodes/<id>/script.txt` + update `metadata.yaml`.
Option B additionally writes `sources_used.yaml` as an audit trail.

Expected output: ~2800–3500 characters, 3–5 `[CHUNK_BREAK]` markers.

## 5. Run TTS

```bash
python scripts/run_tts.py --episode 04_your-episode-slug
```

This generates per-chunk MP3s in `episodes/<id>/tts_chunks/` and the
final concatenated MP3 as `episodes/<id>/<id>_full.mp3`.

Budget: about $0.40–0.60 per episode on ElevenLabs Creator tier.

## 6. Listen end-to-end

Seriously. Every episode, every time. Wear headphones. If the author
doesn't listen, the listeners won't either.

Things to check:
- Chunk boundaries: any awkward prosody jumps?
- Numbers: all pronounced correctly?
- Proper nouns: "Kaplan-Meier", "SPSS", names of people — right?
- Emotional beats: does the [emphasizes] land where it should?

If anything's off, fix the script and rerun TTS for only the affected
chunks — don't redo the whole episode. (Script-level surgery is a
future improvement; for now, rerun the whole script.)

## 7. Fill in metadata.yaml

Update `episodes/<id>/metadata.yaml` with:
- Final `audio.duration_seconds` (from ffprobe)
- Final `audio.size_mb`
- Actual `cost_usd` (check ElevenLabs dashboard for exact)
- Any `notes` about what worked or didn't

## 8. Upload + RSS update

```bash
python scripts/publish.py --episode 04_your-episode-slug \
    --intro static/intro.mp3 \
    --outro static/outro.mp3
```

This will:
1. Splice intro/outro + normalize to -16 LUFS (Apple/Spotify spec)
2. PUT the MP3 to Cloudflare R2
3. Scan all episodes with an `audio.url` in their metadata.yaml,
   rebuild `feed.xml`
4. PUT the feed to R2
5. Print the audio URL + feed URL

For the first episode only, you'll need to submit the feed URL to
Apple Podcasts Connect and Spotify for Creators. After that, both
platforms poll the feed automatically every few hours.

## 9. Promote

Once the episode is live:
- Instagram post with episode card
- Facebook post
- LinkedIn (if professional angle)
- WhatsApp to specific people who might care

The first 10 listeners should come from your DMs, not from Apple
Podcasts' algorithm. Build the audience one listener at a time.
