# The second-brain pattern this brain is built on

Synthesis of the design inputs (Nov 8, 2026). Sources: Walrus X post
Nov 7; Ryven article Oct 27; Karpathy llm.txt gist; 8 public repos
(full verdicts in [attribution](../docs/attribution.md)).

## The core idea

RAG re-derives knowledge from scratch on every question. A wiki
compiles it once and keeps it current: the LLM reads a new source,
extracts what matters, integrates it into the existing pages,
updates cross-references, and flags where new data contradicts old
claims. The cross-references are already there. The contradictions
are already flagged. The synthesis already reflects everything read.
That compounding — not retrieval — is the whole point.

## The shape

- **Three layers:** immutable `raw/` sources, compiled `wiki/`,
  and the schema (the map files) that tells the LLM the conventions.
- **A map, loaded every session**, under 200 lines. Rules load only
  on match; skills run only when called. The map catches conflicts
  (a rule contradicting the map gets flagged, not followed).
- **One topic per file. One idea per note.** Atomic notes: one idea,
  one source, one conclusion, max 3 tags.
- **Every claim keeps its source.** No source, no claim.
- **Duplicates are detected**, not filed twice: SHA-256 exact match,
  Jaccard > 0.72 is a likely duplicate.
- **Five stages:** CURATE → SEARCH → REWRITE → REVIEW → OBSERVE.
- **A weekly loop** instead of a daemon: repeated corrections become
  rules, stale pages get flagged, unused rules retire, Git records
  it all in ≤200-word commits.
- **Plain text only.** Markdown + ripgrep + Git. No Obsidian, no
  database, no embeddings, no vector search, no API keys, no server.

## What was removed, and why

- **Obsidian** (vault, graph view, Dataview, plugins): the graph is
  nice, the Markdown files are the brain. The scan (`scan.py`) and
  the generated map (`MAP.md`) replace the graph view.
- **Databases and embeddings** (gbrain's Postgres, open-second-brain's
  SQLite index, qmd's vectors): the index file plus ripgrep is enough
  at this scale, and a database is a second thing to maintain.
- **Daemons and servers** (gbrain's 24/7 enrichment, smixs's VPS,
  ai-memory's Rust server): a weekly manual pass does the same
  learning without anything running while you sleep.
- **43 skills / 10 agents** (COG): too much surface. Eight skills,
  run when called.
- **The 70/30 lead/lag ratio** (Ryven): named but not verified — not
  applied until its meaning is confirmed.

## Open questions

- One map or two? An earlier version had `MUSE.md` and `CLAUDE.md`
  from two parallel builds. This template merges them into one map
  (`MUSE.md`) — one map is the rule.
- When (if ever) does this brain outgrow index + ripgrep and need
  real search? Karpathy's answer: qmd, later, if the wiki gets big.
  Not now.

Tags: #brain
