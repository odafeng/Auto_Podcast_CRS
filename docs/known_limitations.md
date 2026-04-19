# Known Limitations

Collected during initial build. These are the things that bit us — document
them so we don't re-step on them in three months.

## ElevenLabs v3: no `previous_request_ids`

**What it is**: v3 is the most expressive model with audio tags support,
but it does NOT accept `previous_request_ids` for prosody chaining.

**API response**:
```json
{
  "detail": {
    "type": "validation_error",
    "code": "unsupported_model",
    "message": "Providing previous_request_ids or next_request_ids is not yet supported with the 'eleven_v3' model."
  }
}
```

**Impact**: When splitting a long script into chunks, each chunk is
generated independently. Chunk boundaries may have slight prosody jumps
(different starting energy, different emotional baseline).

**Workarounds considered**:
1. Fall back to `eleven_multilingual_v2` which supports chaining — loses
   expressiveness.
2. Write scripts short enough to fit in one chunk (≤ 3000 chars) — limits
   episode length to ~6-7 minutes.
3. Accept the jumps, use natural paragraph breaks as chunk boundaries so
   the jump feels like a natural pause.

**Current choice**: option 3. Monitor ElevenLabs changelog for v3 chaining
support.

## ElevenLabs v3: 3000 character per-request limit

v3 hard-caps at 3000 chars per request. Multilingual v2 allows 10000.
This is the main reason we chunk.

## ElevenLabs v3 does not preserve voice settings across chunks

When chunk A ends with the voice somewhat excited and chunk B starts from
neutral, there's an audible reset. Mitigation: write scripts so that chunk
breaks fall at natural emotional beats (end of one idea, start of another).

## Apple Podcasts RDAP cannot be queried programmatically

There's no public API to check "is this podcast name already taken" — our
best tool is `web_search` which misses obscure or recent shows. Always
do a manual search in the Apple Podcasts iOS app before committing to a
name.

## Cloudflare R2: public read URL is distinct from S3 write endpoint

Easy to conflate:
- `https://<accountid>.r2.cloudflarestorage.com/<bucket>` → S3-compatible
  write endpoint (requires Access Key ID + Secret)
- `https://pub-<hash>.r2.dev` → public read URL (anonymous)

RSS `<enclosure url>` uses the public read URL. Pipeline PUTs to the
write endpoint.

## Git history keeps secrets forever

If you ever accidentally commit a `.env` file, removing it in a later
commit is NOT enough — the secret is permanently in git history. Rotate
the leaked credentials AND use `git filter-repo` or BFG to scrub history.
Better: never commit, use `.gitignore` religiously.

## Chinese audio in TTS: tone mismatch risk

ElevenLabs v3 handles most Mandarin well, but occasionally mispronounces
tone on ambiguous characters (especially medical terms like 瘺/瘻).
Mitigation: prefer common variants, or use ElevenLabs pronunciation
dictionaries once the vocabulary stabilizes.
