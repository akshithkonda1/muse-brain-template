# Log — what happened, when

Append-only timeline (Karpathy's `log.md`). One line per event.
Prefix every entry the same way so it stays greppable:
`## [YYYY-MM-DD] <kind> | <title>` — kinds: ingest, query, review,
lint, learn, commit, fix. Never rewrite old entries; correct them
with a new entry.

## [2026-11-08] build | Public template created from a scrubbed private brain

- Template built by copying a private second brain, deleting all
  personal notes and facts, and merging two maps (`MUSE.md` +
  `CLAUDE.md`) into one map (`MUSE.md`, 179 lines).
- Ships with 3 example notes only
  (`walrus-second-brain-post`, `example-project`, `example-person`),
  1 example daily note, and placeholder `memory.md` sections.
- No personal data, no secrets, no git history from the private
  brain. Fresh repo — see `SCRUB-REPORT.md` (staging audit file,
  not pushed).
- Design inputs: Walrus X post Nov 7, Ryven X post + article Oct 27,
  Karpathy llm.txt gist, 8 public repos (see `docs/attribution.md`).
