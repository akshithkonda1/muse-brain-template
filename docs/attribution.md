# Attribution — what was borrowed, from where

Read 2026-11-08. All repos public, read-only (cloned to /tmp, nothing
committed or pushed back). Stars/sizes are GitHub's on that date.

## Design inputs (posts)

- **Walrus, @Walrus_systems, Nov 7, 2026** — the map pattern:
  plain Markdown folder, `CLAUDE.md` map under 200 lines loaded every
  session, rules fire only on match, source under every claim,
  conflict flagging, 3,211 → 3,365 records, 11,500+ links, one topic
  per file. No Obsidian, no database. Borrowed whole.
- **Ryven, @imryven, Oct 27, 2026** — "How to Build a Second Brain
  With Claude and Obsidian That Gets Smarter With Every Source You
  Save". Five stages CURATE / SEARCH / REWRITE / REVIEW / OBSERVE;
  folders `raw/`, `wiki/`, `notes/`, `desk/`, `daily/`, `index.md`;
  main map + per-folder instruction files; atomic notes (one idea,
  one source, one conclusion, max 3 tags); duplicate detection
  SHA-256 + Jaccard > 0.72; weekly Git diff/commit ≤200-word summary.
  Borrowed whole, Obsidian removed. "70/30 lead/lag" was named but
  its meaning was not verified from the post — **not applied**;
  do not use it until you confirm what it means.

## The 8 repos

### 1. garrytan/gbrain — 31,733 stars, ~434 MB, MIT
"Give the agent you already use a memory you control." One shared
memory across agents (Claude, Codex, Grok Bot, Muse), every fact
keeps its source, corrections and withdrawal supported, synthesis
layer with citations and gap analysis, typed knowledge graph.
**Borrowed:** provenance + corrections as first-class; the memory
rule in the maps. **Dropped:** the daemon, the database (Postgres),
semantic search / embeddings, MCP server, hosted option — a 434 MB
repo with a server is the opposite of this brain's plain-files rule.
**Obsidian-dependent?** No — but database-dependent, which is the
same kind of weight here. Verdict: ideas yes, code no.

### 2. Karpathy llm.txt gist — idea file, ~12 KB
"The LLM Wiki": RAG re-derives knowledge every query; a wiki
compiles it once and keeps it current. Three layers (raw sources /
wiki / schema), operations ingest / query / lint, `index.md` +
`log.md`, index-first retrieval works at moderate scale without
embeddings. Obsidian is "the IDE" for browsing, explicitly optional.
**Borrowed:** the whole architecture — it is the spine of this
brain. **Dropped:** nothing; the Obsidian tips (graph view, Dataview,
clipper) are noted as optional, not used.

### 3. akitaonrails/ai-memory — 15,408 stars, ~48 MB, Rust, MIT
Long-term memory for coding agents; one shared memory across 20+
harnesses, handoff protocol (quit Claude Code mid-task, resume in
Codex), durable-pages discipline (deliberate writes only, explicit
user request for permanent notes).
**Borrowed:** handoff thinking (the brain, not a harness, is the
continuity) and the durable-pages rule. **Dropped:** the Rust server,
the MCP/hook machinery, cross-machine sync. **Obsidian?** No.

### 4. smixs/agent-second-brain — 417 stars, Python
Telegram voice note → typed, linked knowledge in an Obsidian vault,
24/7 on a $5 VPS, long-lived interactive Claude session to dodge
per-token billing. Vault has `MEMORY.md`, rules per note type
(daily/goals/thoughts/weekly-reflection), inbox-processor + 
note-organizer agents.
**Borrowed:** the per-type rules idea (`rules/`), the inbox →
organize flow. **Dropped:** Telegram bot, VPS daemon, the billing
workaround. **Obsidian-dependent?** Yes — the vault IS Obsidian;
without it this is just the rules files.

### 5. huytieu/COG-second-brain — 1,350 stars, 43 skills, 10 agents
"Self-evolving second brain… just .md files that think." No database,
no vendor lock-in. Skills as recipes, 6 worker agents + 4 read-only
verifier agents, V-model verification harness (opt-in), people CRM.
**Borrowed:** skills-as-recipes; two verification habits — verify by
observing the artifact (never re-read a worker's summary) and a
worker never grades its own homework. **Dropped:** 43 skills and 10
agents (too much surface for a personal brain), the V-model harness,
iCloud/Obsidian Tasks sync. **Obsidian?** Named in the title, but the
files are plain Markdown — usable without it.

### 6. itechmeat/open-second-brain — 523 stars, Bun/TS
Memory layer living in an Obsidian vault; agents read/write via MCP
or the `o2b` CLI; a deterministic "dream" pass turns repeated
signals into rules and retires unused ones (no model inside the
algorithm); `Brain/active.md` carries rules into the next session.
**Borrowed:** the dream pass, as a weekly manual review (repeated
corrections → rules; unused rules retired). **Dropped:** MCP servers,
CLI, SQLite search index, the vault. **Obsidian-dependent?** Yes —
the vault is the store.

### 7. jessepinkman9900/claude-second-brain — 52 stars, npx scaffold
One `npx` scaffolds Obsidian + Claude Code + qmd local search, GitHub
as source of truth, five page types, YAML frontmatter, `/brain-ingest`.
Explicitly "inspired by Karpathy's approach".
**Borrowed:** the Karpathy link confirms the pattern; the five-stage
ingest flow. **Dropped:** the npx scaffold itself, qmd (vector +
BM25 search — embeddings, out of scope), the Obsidian vault.
**Obsidian-dependent?** Yes — the scaffolded folder IS the vault.

### 8. naveedharri/baalda — 304 stars, Tauri/Rust, Apache-2.0
"The team second brain." Plain Markdown files on disk, editable by
AI like a teammate, shared in real time (CRDTs + files). Scanned 41
Obsidian-like apps against 12 requirements; none satisfied all 12.
**Borrowed:** the proof that plain Markdown files can be the whole
store, human + agent editing the same files. **Dropped:** the app
itself (real-time collaboration is not this brain's job — Git is).
**Obsidian?** No — it is an Obsidian alternative.

## What was deliberately NOT taken from anywhere

- No Obsidian (vault, graph, Dataview, plugins, obsidian-git).
- No database of any kind (Postgres, SQLite index, vector DB).
- No embeddings, no semantic search, no reranking.
- No API calls at ingest or review (no Gemini CLI, no Mistral OCR).
- No daemons, crons, VPS, or always-on servers.
- No npx scaffolding that pulls in a stack.
- No 43-skill / 10-agent surface. Eight skills, run when called.
