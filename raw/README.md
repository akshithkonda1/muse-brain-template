# raw/ — immutable sources

The source of truth. Articles, files, links, transcripts that the
wiki is built from. **Never edited, never rewritten.** If a source
is wrong, the correction goes in `wiki/` / `notes/` with a source —
`raw/` stays as it was when it arrived.

## Conventions

- One source per file: `raw/YYYY-MM-DD-<slug>.md`.
- Each file starts with: source URL or origin, author, date, and a
  short summary. Full verbatim copies only when the source is short
  and your own; for links, summary + URL, not a scrape.
- Images go in `raw/assets/` (see Karpathy's tip — download them
  locally so links do not rot).

## Sources on file

- Walrus X post, Nov 7, 2026 — the map pattern.
  https://x.com/walrus_systems/status/2119163389897322712
- Ryven X post, Nov 8, 2026 + article Oct 27, 2026 — the five stages.
  https://x.com/imryven/status/2119433356584604119
  https://x.com/imryven/status/2115046979659055476
- Karpathy, "LLM Wiki" idea file (gist).
  https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- The 8 repos: see `docs/attribution.md` for the list and verdicts.
  (Not cloned here — your own repos, when you add them, are
  what get ingested; these references were design input only.)
