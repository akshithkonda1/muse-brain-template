# ML — local-first machine learning for Muse Brain

Added Nov 2026, as an optional layer on the plain-Markdown brain.
Everything else stays plain Markdown + ripgrep + Git.

## What it does

| Command | What you get |
|---|---|
| `python3 -m ml.search "query"` | Ranked search: BM25 primary, TF-IDF cosine second |
| `python3 -m ml.search --related <stem>` | Notes most related to one note |
| `python3 -m ml.search --suggest-links` | Unlinked pairs worth linking |
| `python3 -m ml.search --clusters` | Topic clusters, labelled by top terms |
| `python3 -m ml.search --duplicates` | Exact (SHA-256) + Jaccard > 0.72 + semantic (cosine > 0.85) |
| `python3 -m ml.search --conflicts` | Possible tensions — heuristic flag, review by hand |
| `python3 -m ml.search --all` | Every report (used by the memory map) |
| `python3 -m ml.embeddings "query"` | Embedding search, if the optional libs are installed |

Run from the repo root. Add `--json` for machine-readable output.
The Muse trigger is `"brain: ml search <query>"` — see
`skills/ml-search/SKILL.md` and `docs/commands.md`.

## Why TF-IDF + BM25 first

At small scale an index plus word overlap is enough, and it is
explainable: every score can be traced to shared words. BM25
handles length differences between short and long notes; TF-IDF
cosine handles relatedness and clustering. Embeddings are a second
signal for paraphrase queries ("same idea, different words") where
word overlap fails — useful, not required.

## Optional embeddings (local only)

```bash
pip install sentence-transformers numpy
```

First run downloads `all-MiniLM-L6-v2` (~90 MB) from Hugging Face
and then runs fully offline. `ml/embeddings.py` encodes the corpus,
caches it in `ml/.cache/embeddings.npz`, and invalidates the cache
whenever any note is newer than the cache. If the libraries are not
installed, every embeddings call returns empty and prints the
fallback notice — the TF-IDF/BM25 baseline keeps working.

## Privacy — the whole point

- **No external API calls. No cloud. No keys. No daemon, no server.**
- The model (if installed) runs on this machine, on files already
  in the repo. Nothing leaves the machine.
- Generated caches (`ml/.cache/`, `*.npz`, `*.npy`, `*.pkl`) are
  gitignored and must never be committed. Check with
  `git status` before any commit — the cache must not appear.

## How the memory map uses it

`python3 scripts/memory-map.py` runs the ML reports (clusters,
link suggestions, duplicates, tensions) and writes them into
`MEMORY-MAP.md`, then re-runs `scan.py` so `MAP.md` and
`dashboard.html` match. `MEMORY-MAP.md` is generated — never edit
it by hand.

## Limits, stated plainly

- TF-IDF cannot see synonyms or paraphrase; that is what the
  optional embeddings are for.
- Clustering is greedy and threshold-based (cosine ≥ 0.15 joins a
  cluster — tuned on a ~45-note corpus; 0.30 left almost everything
  a singleton, 0.10 over-merged into grab-bags). Re-tune the
  threshold in `ml/search.py` if the clusters stop being useful.
- Conflict detection is a heuristic (similar topic + disjoint tags
  + a negation marker). It flags things for you to review; it
  never decides a contradiction on its own.
