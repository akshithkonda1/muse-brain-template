---
name: brain-ml-search
description: "ML search over Muse Brain: ranked search, related notes, link suggestions, clusters, duplicates. Trigger: 'brain: ml search <query>'."
---

# ML search

Local-first ML ranking over the brain. Baseline is stdlib TF-IDF +
BM25 (`ml/search.py`) — always available, no installs, no API.
Optional local embeddings (`ml/embeddings.py`) add a second signal
when `sentence-transformers` + `numpy` are installed; if they are
not, say so and use the baseline. Nothing here calls a cloud
service, and no note ever leaves the machine.

## Steps

1. **Run the tool, don't guess.** From the repo root:
   - Ranked search: `python3 -m ml.search "<query>"` (BM25 + cosine)
   - Related to one note: `python3 -m ml.search --related <stem>`
   - Link suggestions: `python3 -m ml.search --suggest-links`
   - Clusters: `python3 -m ml.search --clusters`
   - Duplicates: `python3 -m ml.search --duplicates`
   - Possible tensions: `python3 -m ml.search --conflicts`
   - Everything: `python3 -m ml.search --all`
   - Embeddings (optional): `python3 -m ml.embeddings "<query>"`
2. **Report scores with the answer.** A result is a note plus its
   BM25 / cosine score — the score is the evidence the ranking is
   real, not a vibe. If the top score is low (< ~1.0 combined),
   say the match is weak.
3. **Link suggestions are suggestions.** Propose the `[[link]]`;
   add it only if you agree or the link is obviously right (the
   two notes already cite the same source). Never auto-link.
4. **Duplicates:** exact (SHA-256) or Jaccard > 0.72 means link to
   the existing page, don't write a new one. A semantic
   near-duplicate (cosine > 0.85) means read both pages before
   deciding — they may be two sides of one topic.
5. **Tensions are flags, not verdicts.** A flagged pair goes to you
   (or the weekly review) as "these two look in tension — which is
   right?" Never resolve one silently.
6. **After any change to the notes, re-run the map:**
   `python3 scripts/memory-map.py` (regenerates MEMORY-MAP.md,
   MAP.md, and dashboard.html).

## Rules

- Never answer from chat memory when the brain has a page on it.
- Never send note text anywhere: no API, no paste, no upload.
- If the optional embeddings are missing, do not pretend they ran.
  Say "embeddings not installed — TF-IDF/BM25 result" and carry on.
- Embedding caches live in `ml/.cache/` (gitignored). If one ever
  shows up in `git status`, stop and fix the ignore before
  committing.
