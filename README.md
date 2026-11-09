# Muse Brain — template

A plain folder of Markdown notes that works as a living second brain,
built for Muse and adapted from the pattern in the Walrus X post of
Nov 7, 2026 (@walrus_systems): a solo builder turned a folder of
Markdown into a graph that lights up when the map loads.

This is a **template, not someone's brain**. It ships with example
notes only — no personal data. Copy it, delete the examples, and seed
it with your own notes. Your filled-in brain should live in a
**private** repo; this template is the public, shareable shape.

What changed in the adaptation:

- **Muse in for Claude.** The map file is `MUSE.md`, not `CLAUDE.md`.
  Same role: the loaded map of the brain, under 200 lines.
- **Obsidian out.** No Obsidian, no plugins, no vault. Plain Markdown
  files, `[[wiki-links]]` as plain text, one Python script for the scan.
- **One map.** An earlier version had two maps (`MUSE.md` + `CLAUDE.md`)
  from two parallel builds. This template merges them into `MUSE.md`
  alone. If you fork this and add a second map, merge it back — one map
  is the rule.

## Layout

| Path | What it is |
| --- | --- |
| `MUSE.md` | The loaded map. Read first. Under 200 lines. |
| `MAP.md` | Generated index of all notes by tag + link graph. Never edit by hand. |
| `dashboard.html` | Generated simple dashboard (tree by tag, counts, recent notes). No external assets. |
| `scan.py` | The one scan command. Python stdlib only. |
| `notes/` | The notes. One topic per file. Three example notes included — delete them when you seed your own. |
| `raw/` | Immutable sources. Never edited, never rewritten. |
| `wiki/` | Compiled synthesis. See `wiki/second-brain-pattern.md`. |
| `desk/` | Working surface. Drafts and half-formed thinking. |
| `daily/` | Day pages. One example included. |
| `memory.md` | Durable facts, every claim with a source. Template only — fill it in. |
| `index.md` | Hand catalog. `log.md` — append-only timeline. |
| `rules/` | People rules + writing rules. Load only on match. |
| `skills/` | Eight skills (`ingest`, `search`, `ask`, `learn`, `rewrite`, `lint`, `commit`, `weekly-review`). Run when called. |
| `templates/` | Note templates (atomic note, daily, person, project). |
| `scripts/dup-check.py` | Duplicate check (SHA-256 + Jaccard > 0.72). |
| `docs/` | `attribution.md` (what was borrowed from which repo) and `commands.md` ("brain: …" trigger map). |

## How to add a note

1. Create `notes/<kebab-case>.md`. First line is a `# Title`.
2. Keep it tight: what it is, key facts with sources, links to related
   notes with `[[wiki-links]]` (e.g. `[[example-person]]`,
   `[[example-project]]`).
3. End the file with a `Tags:` line using 1–3 tags from the set:
   `#brain` `#notes` `#projects` `#journal` `#people` `#places`
   `#ideas` `#goals` `#money`.
4. Run the scan so the map picks it up.

Example note skeleton:

```markdown
# Topic name

One line on what this is.

- Fact, with source. (Source: <where>, YYYY-MM-DD)
- Fact that links onward. See [[related-note]].

## Open threads

- [ ] Something still owed.

Tags: #projects #goals
```

## How to run the scan

From this folder:

```bash
python3 scan.py
```

It walks `notes/`, extracts tags and `[[links]]`, and regenerates `MAP.md`
and `dashboard.html`. It prints a summary: note count, per-tag counts,
link count, broken links, and orphans (notes with no links in or out).
Fix broken links by correcting the `[[target]]` or creating the note.
Orphans are fine for inbox-style notes; everything else should link.

## The rules (short form)

Full version lives in `MUSE.md`.

1. Sources under every claim.
2. Grounded reasoning — your actual data, never averages or invention.
   Name the gap when something is missing.
3. Balanced thinking — keep live tensions visible, don't resolve them
   quietly.
4. Structured output — tight notes, no filler.
5. Correct only what was corrected.

Hard lines: never message anyone without explicit permission; money is
read-only; never book, pay, submit, or send without a go-ahead on the
exact text or action; no secrets or keys in the repo; health detail
stays out of the brain by design; never touch a live shared document.

## Weekly review

See `skills/weekly-review/SKILL.md`. Once a week it sweeps the open
threads, stale pages, orphans, conflicts, and duplicates, and produces
a short structured review. Health is excluded by design.
