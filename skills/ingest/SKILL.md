---
name: brain-ingest
description: "File a new source into Muse Brain: raw → wiki → atomic note → index + log. Trigger: 'brain: ingest <source>'."
---

# Ingest

File one source at a time; stay involved — you read the summary
and guide what to emphasize (Karpathy's rule).

## Steps

1. **Capture.** Save the source in `raw/` under a dated, kebab-case
   name (`raw/2026-11-08-<slug>.md`). Never edit it afterwards.
   For a link, save the URL, author, date, and a short summary — not a
   full verbatim copy. For a file you hand over, save it as-is.
2. **Read.** Read the source fully. Discuss the key takeaways with
   you if you are present; otherwise note them.
3. **Dedup first.** Run `python3 scripts/dup-check.py` for the topic.
   If a note already covers it, update that note — do not file a second.
4. **Write the atomic note** in `notes/` (see `templates/atomic-note.md`):
   one idea, one source, one conclusion, max 3 tags, `[[links]]`.
5. **Update the wiki.** Touch every `wiki/` page the source affects
   (often 1–3 pages, not 15 at this scale): update entity/concept
   pages, note where new data contradicts old claims, strengthen or
   revise the synthesis. Strike through superseded claims; never
   silently rewrite them.
6. **Update `index.md`** (one line per new/changed page) and append a
   `## [YYYY-MM-DD] ingest | <title>` line to `log.md`.
7. **Run `python3 scan.py`** so `MAP.md` and the dashboard pick it up.

## What not to do

- Do not ingest without a source. A claim with no source is a
  `[source needed]` placeholder, not a fact.
- Do not batch-ingest a pile of sources unsupervised on the first pass.
- Do not copy private memory files wholesale into the brain. Summarize
  with sources; the full record stays where it is.
- No API calls, no OCR, no model inside the filing step. Reading and
  writing are the agent's job; the scripts only check and count.
