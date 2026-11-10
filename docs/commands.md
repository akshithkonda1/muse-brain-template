# Commands — "brain: …" trigger map

Muse has no Claude Code slash-commands, so the Ryven
`/project:second-brain:*` commands are plain phrases instead.
Say the phrase in the Muse Brain chat (or any chat with this folder
loaded); Muse reads the matching skill and follows it.

| You say | Skill run | What happens |
|---|---|---|
| "brain: ingest <link, file, or text>" | `skills/ingest/` | Source → `raw/`, wiki updated, atomic note, index + log |
| "brain: search <query>" | `skills/search/` | ripgrep + index first, then the matching pages |
| "brain: ml search <query>" | `skills/ml-search/` | TF-IDF/BM25 ranked search; related, clusters, dups |
| "brain: login" | — | Open the sign-in screen (see `docs/login.md`) — local-first; "Sign in with Muse" is an honest placeholder until Meta publishes an endpoint |
| "brain: knows <topic>" | `skills/what-muse-knows/` | What Muse knows about a topic: one-line summary + source trail, from the notes |
| "brain: related <note>" | `skills/ml-search/` | Notes most related to one note (`--related`) |
| "brain: suggest links" | `skills/ml-search/` | Unlinked pairs worth linking (`--suggest-links`) |
| "brain: clusters" | `skills/ml-search/` | Topic clusters from the ML step |
| "brain: map" | — | Run `python3 scripts/memory-map.py` (regenerates MEMORY-MAP.md, MAP.md + dashboard) |
| "brain: package" | — | Run `python3 scripts/package.py` (clean downloadable zip in `dist/`) |
| "brain: app" | — | Run `python3 app/app.py` (local server + dashboard; `.exe`/`.dmg` in `docs/installers.md`) |
| "brain: build dmg" | — | macOS: Swift/SwiftUI app → `.dmg` via `xcodebuild` + `hdiutil` (or CI job `build-macos`) |
| "brain: build exe" | — | Windows: React Native Windows app → `.exe` via `run-windows --release` (or CI job `build-windows`) |
| "brain: ask <question>" | `skills/ask/` | Cited answer from the wiki; good answers filed back |
| "brain: learn <correction>" | `skills/learn/` | Correction → rule or memory entry, old claim struck |
| "brain: rewrite <page>" | `skills/rewrite/` | Tighten the page in your voice, sources kept |
| "brain: weekly review" | `skills/weekly-review/` | Stale / orphan / conflict / duplicate sweep |
| "brain: lint" | `skills/lint/` | Contradictions, stale claims, missing links |
| "brain: commit" | `skills/commit/` | Diff review, commit with ≤200-word summary |
| "brain: scan" | — | Run `python3 scan.py` (regenerates MAP.md + dashboard) |
| "brain: dup check" | — | Run `python3 scripts/dup-check.py` |

## Notes on the mapping

- Ryven's five stages map to skills: CURATE → `ingest`, SEARCH →
  `search`, REWRITE → `rewrite`, REVIEW → `weekly-review` + `lint`,
  OBSERVE → `log.md` (every run logs one line).
- There is no background daemon, no cron, no server. Every skill
  runs because you (or a scheduled Muse run you approved) asked
  it to. The "dream pass" is the weekly review, done by hand.
- `scan.py` is the one scan command for the `notes/` layer: it walks
  `notes/`, extracts tags and `[[links]]`, regenerates `MAP.md` and
  `dashboard.html`, and prints counts, broken links, and orphans.
- ML is local-first (added Nov 2026): the `ml/` baseline is stdlib
  TF-IDF/BM25, no installs, no API calls. Optional local embeddings
  (`sentence-transformers`) add a second ranking signal and fall
  back gracefully when absent. Embedding caches live in `ml/.cache/`
  (gitignored, never committed). `scripts/memory-map.py` is the full
  memory map: every file, tags, links in/out, ML clusters, sources,
  stale flags — generated, never hand-edited. It re-runs `scan.py`
  so MAP.md matches.
- Nothing here calls an API, spends money, or needs a key. Search is
  ripgrep (`rg`) over Markdown; if `rg` is missing, `grep -r` works.
