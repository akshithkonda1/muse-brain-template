# Index — catalog of the wiki

Content catalog (Karpathy's `index.md`): what the brain holds, one
line per page, by area. The generated link graph is `MAP.md`
(rebuilt by `python3 scan.py` — never edit by hand). This file is
hand-maintained; update it on every ingest.

## System

- [MUSE.md](MUSE.md) — the map. Read first. The only map.
- [MAP.md](MAP.md) — generated index (rebuilt by `python3 scan.py` —
  never edit by hand)
- [Memory](memory.md) — durable facts, every claim with a source
- [Log](log.md) — timeline of ingests, queries, reviews
- [README](README.md) — how the system works

## Example notes (delete when you seed your own)

- [Walrus second-brain post](notes/walrus-second-brain-post.md) —
  worked example of an atomic note (public post, no personal data)
- [Example project](notes/example-project.md) — fictional project note
- [Example person](notes/example-person.md) — fictional person note

## Layers

- `notes/` — atomic notes, one topic per file
- `raw/` — immutable sources · `wiki/` — compiled synthesis
- `desk/` — working surface · `daily/` — day pages
- `rules/` — people + writing rules · `skills/` — eight skills
- `MUSE.md` — the map · `scan.py` — the one scan command
