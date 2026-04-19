# Producing a New Episode — Workflow

For future you, after the initial scaffolding is done.

## 1. Create the episode folder

```bash
mkdir -p episodes/04_your-episode-slug
```

Naming: `NN_kebab-case-slug` where NN is zero-padded episode number.

## 2. Put the source material in

### For a WordPress-based episode
Copy the blog post body into `source.md`. (Once the WordPress fetcher
is implemented, this step will be automatic.)

### For a prompt-driven episode
Skip `source.md`. Instead, write your brief (target audience, structure,
what to say) directly at the bottom of this workflow doc, and pass it
into the Claude API yourself.

## 3. Choose a prompt version

| Prompt version | Use when |
|---|---|
| `v1_generic` | Adapting a first-person manifesto-style blog post |
| `v1_persuasion` | Convincing someone on the fence about doing X |
| `v1_onboarding` | Giving a concrete, prescriptive first-day guide |

## 4. Generate the script

```bash
python scripts/generate_script.py \
    --episode 04_your-episode-slug \
    --prompt-version v1_generic \
    --episode-kind manifesto
```

Review `episodes/04_your-episode-slug/script.txt`. Expected output:
~2800–3500 characters, a few `[CHUNK_BREAK]` markers.

If you don't like it, tweak the prompt under `auto_podcast_crs/scripts/prompts/`
and regenerate. Or rewrite the script manually — the pipeline doesn't
care who wrote it.

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

## 8. Upload + RSS update (not yet implemented)

Once R2 storage and RSS feed builder are done:

```bash
python scripts/publish.py --episode 04_your-episode-slug
```

This will:
1. PUT the MP3 to Cloudflare R2
2. Update the RSS feed XML and PUT that to R2
3. Print the public URL
4. (Optional) Ping Apple Podcasts to refresh the feed

## 9. Promote

Once the episode is live:
- Instagram post with episode card
- Facebook post
- LinkedIn (if professional angle)
- WhatsApp to specific people who might care

The first 10 listeners should come from your DMs, not from Apple
Podcasts' algorithm. Build the audience one listener at a time.
