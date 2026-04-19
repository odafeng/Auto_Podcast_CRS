# Preparing Resources for a Topic-Based Episode

If you're using `scripts/generate_from_topic.py`, the script needs reference
material to synthesize from. This is where you curate it.

## Layout

For episode `04_my-slug`:

```
episodes/04_my-slug/
├── resources/          ← put your files here
│   ├── smith_2024_robotic_lc.md
│   ├── chen_2023_meta.md
│   └── my_own_notes.md
├── script.txt          ← generated
├── sources_used.yaml   ← audit trail
└── metadata.yaml       ← auto-updated
```

## What goes in `resources/`

Accepted file types: `.md`, `.markdown`, `.txt`. Skipped silently: everything
else (PDFs, images, binaries).

Typical contents:
- **Papers** you've read and want to reference. Paste the abstract + key
  findings into a markdown file. You don't need to include the whole paper —
  the script is 10 minutes long, not a systematic review.
- **Your own notes** on a topic. Bullet points of observations, opinions,
  anecdotes you want to make sure land in the episode.
- **Clinical guidelines** or society statements (NCCN, ASCRS, EAES).
- **Previous ep scripts** if you want to reference them ("as I said in ep02…").

## What does NOT go in `resources/`

- Full PDFs (parse them to .md first — tools like `pdf-reading` skill or a
  simple `pdftotext` work)
- Images, figures (the script is audio; figures aren't spoken)
- Patient data in any form (see `docs/known_limitations.md`)
- The whole of PubMed

## How many files?

2–5 is the sweet spot. Fewer → Claude doesn't have enough to synthesize
from. More → the script flattens into "here's finding 1, here's finding 2,
here's finding 3…" because it tries to honor every source.

If you have more than 5 files, pick the ones that bring distinct angles
(e.g., one pro, one con, one meta-analysis, one mechanism paper). Drop the
redundant ones.

## How long can each file be?

The loader caps the total at ~400k estimated tokens (half of Claude Sonnet
4.6's context window). That's roughly 600,000 Chinese characters or 1.6M
English. You will not hit this in practice.

If you do, the loader errors out with a clear message. Trim the files and
try again.

## Reproducibility

The `resources/` folder is **git-tracked per episode**. This is deliberate
— when you want to regenerate ep04 a year from now, or hand it to a
collaborator, the exact source material is right there next to the script.

`sources_used.yaml` records what was actually loaded at generation time
(filename + char count per file). Treat it as the bibliography for that
episode.

## Naming convention (suggested, not enforced)

```
<author>_<year>_<short_topic>.md    # e.g. smith_2024_robotic_lc.md
my_notes_<topic>.md                 # e.g. my_notes_pelvis_anatomy.md
society_<name>_<year>.md            # e.g. society_eaes_2023.md
```

Stable naming helps future-you remember what each file is. The loader sorts
alphabetically, so you can also use numeric prefixes (`01_key_paper.md`) to
control ordering if that matters.
