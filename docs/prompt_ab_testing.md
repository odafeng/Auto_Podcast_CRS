# Prompt A/B Evaluation Protocol

This is the process for comparing prompt versions (e.g. v1 vs v2) so we
don't end up adopting a "new" prompt that actually reads worse.

## Why this exists

We ship versioned prompts (`system_v1_*.md`, `system_v2_*.md`, ...).
Every new version claims to be better. Without a real comparison, we
end up trusting vibes. That's fine once, not fine across 10 episodes.

## The protocol

For each new prompt version, before promoting it to default:

### 1. Pick 3 source articles as the test set

Use source material you've **already shipped** so you know what
"acceptable" sounds like. For v2, that means:
- `episodes/01_why-surgeons-should-code/source.md` (manifesto)
- `episodes/02_python-for-hesitant-physician/source.md` (persuasion)
- `episodes/03_your-first-week-with-python/source.md` (onboarding)

### 2. Generate the new version

For each article, generate the v2 script:
```bash
python scripts/generate_script.py --episode 01_v2_test \
    --blog-path episodes/01_why-surgeons-should-code/source.md \
    --prompt-version v2_generic
```

Keep the output in a temporary folder like `episodes/ab_test/`.

### 3. Run TTS for both versions on the same voice

Generate MP3 for both v1 and v2 scripts. This is critical — you're
comparing **audio**, not text. A script that reads fine can sound like
a robot, and vice versa.

Budget: 6 scripts × ~$0.40 = ~$2.40 for the whole comparison.

### 4. Blind listening test

Put both MP3s in a folder with neutral names (`a.mp3`, `b.mp3`).
**Don't label which is which.** Listen to both with headphones.

For each pair, rate on three axes (1–5):
- **Naturalness** — does it sound like a person, or a narrator reading?
- **Clarity** — is the core message coming through?
- **Energy** — does the voice maintain engagement, or drift into monotone?

Record ratings in a yaml file like:

```yaml
# ab_test_2026-04-19.yaml
test_set:
  - article: ep01
    v1_rating:
      naturalness: 3
      clarity: 5
      energy: 3
    v2_rating:
      naturalness: 4
      clarity: 4
      energy: 4
    notes: |
      v1 was clearer but sounded like a TED talk.
      v2 felt more like a real colleague talking, but buried the main point.
      Net: v2 wins on naturalness, v1 wins on clarity.
```

### 5. Decision rule

v2 becomes the new default only if:
- Mean naturalness score across the 3 articles ≥ v1 score + 0.5, AND
- Mean clarity score across the 3 articles ≥ v1 score − 0.3

(Some clarity regression is acceptable if naturalness jumps. A lot of
regression is not.)

If v2 fails this bar, don't promote. Iterate on the prompt and retest.

### 6. Retain the losing version

Do **not** delete the old prompt. It's the reproducibility record for
previously-shipped episodes, and you may want to fall back to it for
specific article types later.

## Edge cases

- **Tie:** keep v1 as default. The bar for switching should be meaningful.
- **v2 wins one axis, v1 wins another:** don't promote v2 as universal
  default. Consider keeping both and making the choice per-episode-type.
- **Scores feel random:** you probably listened to both once in a row.
  Do the test on separate days, or have someone else listen blind.

## What this protocol is NOT

- It's not a replacement for listening to every final episode (you still
  do that before publishing — see `workflow.md` step 6).
- It's not a guarantee the chosen prompt is objectively best. It's a
  guardrail against vibes-based prompt upgrades.
- It's not automated. Audio quality is still a human judgment call.
