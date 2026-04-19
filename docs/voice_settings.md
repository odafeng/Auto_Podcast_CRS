# Voice Tuning Notes

Empirical observations from generating the first three episodes with
`eleven_v3` + a cloned voice (Instant Voice Clone, not PVC).

## Current settings

- Model: `eleven_v3`
- Output format: `mp3_44100_128`
- Voice settings: defaults (no explicit `voice_settings` override)
- Audio tags used: `[pauses]`, `[emphasizes]`, `[thoughtful]`, `[laughs]`

## What works well

- Mandarin-English code-switching: clean on technical terms
  (SPSS, Cox regression, pipeline, forest plot, overfitting)
- Numbers: "8 週"、"12 週"、"100 個病人" read correctly
- Self-deprecating humor: `[laughs]` tag produces natural chuckle,
  not a canned laugh
- Emphasis: `[emphasizes]` adds real prosodic stress, not just volume

## What doesn't work yet

- **Cross-chunk prosody**: each chunk starts from "cold" — see
  docs/known_limitations.md
- **Sustained excitement**: v3 tends to regress to neutral within a
  paragraph, even with `[excited]` tag at start
- **Regional vocabulary**: Taiwanese-specific terms sometimes get
  read with Mainland intonation

## Audio tag usage guidelines (provisional)

These are heuristics that seemed to work. Revisit after more episodes.

| Tag | Good use | Bad use |
|---|---|---|
| `[pauses]` | Before a warning, before a key number | Every paragraph |
| `[emphasizes]` | On the single most important sentence of a section | On every conclusion |
| `[thoughtful]` | Rhetorical question, reflection | Explanations |
| `[laughs]` | Self-deprecating moment | Formal content |

Rule of thumb: **one audio tag per 150-200 characters of script**.
More than that starts feeling like an overacting voice actor.

## Future experiments

- [ ] Try `voice_settings` with `stability=0.5, similarity_boost=0.85` to
      see if chunk-to-chunk consistency improves
- [ ] Upgrade Instant Voice Clone (IVC) to Professional Voice Clone (PVC)
      — requires 30min+ of sample audio, but meaningfully improves
      consistency
- [ ] Test `eleven_multilingual_v2` head-to-head with v3 on the same
      script, A/B the audio
