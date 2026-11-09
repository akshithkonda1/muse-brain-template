---
name: brain-search
description: "Search Muse Brain for what it knows. Trigger: 'brain: search <query>'."
---

# Search

Search is ripgrep over Markdown plus the index — no embeddings, no
vector DB (Karpathy: the index is enough at this scale). For ranked /
semantic search, related notes, and clusters, use the ML skill
instead: `skills/ml-search/` ("brain: ml search <query>") — local
TF-IDF/BM25 by default, optional local embeddings, no API.

## Steps

1. **Index first.** Read `index.md` and find the pages the query
   points at. Then read those pages.
2. **Ripgrep second.** `rg -i "<query>" wiki/ notes/ memory.md` —
   case-insensitive, with context (`-C 2`). If `rg` is missing,
   `grep -ri` works. Search `raw/` only when the compiled pages do
   not answer it.
3. **Answer from the pages, with citations.** Every claim in the
   answer names the page (and source) it came from. Say plainly what
   the brain does not know — the gap is part of the answer (gbrain's
   gap analysis, without the synthesis server).
4. **If the answer is thin:** say what source would fill it and ask
   you whether to ingest it. Do not invent the missing piece.

## Rules

- Never answer from chat memory when the brain has a page on it.
  The brain is the record; chat is the conversation.
- Do not search the whole brain on every query. Index → pages →
  ripgrep. Load only what the query needs.
