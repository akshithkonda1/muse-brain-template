# Commands — "brain: …" trigger map

Muse has no Claude Code slash-commands, so the Ryven
`/project:second-brain:*` commands are plain phrases instead.
Say the phrase in the Muse Brain chat (or any chat with this folder
loaded); Muse reads the matching skill and follows it.

| You say | Skill run | What happens |
|---|---|---|
| "brain: ingest <link, file, or text>" | `skills/ingest/` | Source → `raw/`, wiki updated, atomic note, index + log |
| "brain: search <query>" | `skills/search/` | ripgrep + index first, then the matching pages |
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
- Nothing here calls an API, spends money, or needs a key. Search is
  ripgrep (`rg`) over Markdown; if `rg` is missing, `grep -r` works.
