#!/usr/bin/env python3
"""ml/embeddings.py — OPTIONAL local embeddings for Muse Brain.

This module is optional by design. The TF-IDF/BM25 baseline in
ml/search.py always works with zero extra dependencies. Embeddings
add a second ranking signal for paraphrase-style queries ("same
idea, different words"), where word overlap fails.

Requirements (only if you want this path):
  pip install sentence-transformers numpy
  # model "all-MiniLM-L6-v2" (~90 MB) downloads once, on first use,
  # from Hugging Face, and then runs fully offline on this machine.

Privacy: the model runs locally. Notes never leave the machine, no
API calls, no keys. The embedding cache lives in ml/.cache/ — it is
gitignored and must never be committed (see .gitignore).

If the libraries are not installed, every function here returns
None / an empty result and prints a short note telling you the
fallback (TF-IDF/BM25) is in use. Nothing else breaks.

Usage:
  from ml.embeddings import available, search
  if available():
      for stem, score in search("my query", docs):
          ...
  # or from the repo root:
  python3 -m ml.embeddings "my query"
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = Path(__file__).resolve().parent / ".cache"
MODEL_NAME = "all-MiniLM-L6-v2"


def available() -> bool:
    """True only if both optional libraries import cleanly."""
    try:
        import numpy  # noqa: F401
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


def _load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def _cache_path():
    return CACHE_DIR / "embeddings.npz"


def _docs_changed(docs) -> bool:
    """True if the cache is missing or any doc is newer than it."""
    cache = _cache_path()
    if not cache.exists():
        return True
    cache_mtime = cache.stat().st_mtime
    for d in docs:
        p = ROOT / d["file"]
        if p.exists() and p.stat().st_mtime > cache_mtime:
            return True
    return False


def encode_docs(docs):
    """Encode docs to a numpy matrix, cached in ml/.cache/.

    Returns None when the optional libraries are absent.
    Cache key is file mtimes: any edited doc invalidates the cache.
    """
    if not available():
        print("Embeddings not installed (sentence-transformers / numpy "
              "missing). Falling back to TF-IDF/BM25 — see ml/README.md.",
              file=sys.stderr)
        return None
    import numpy as np

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    texts = [d["title"] + "\n" + d["text"] for d in docs]
    if not _docs_changed(docs):
        data = np.load(_cache_path(), allow_pickle=False)
        if data["emb"].shape[0] == len(docs):
            return data["emb"]
    model = _load_model()
    emb = model.encode(texts, normalize_embeddings=True,
                       show_progress_bar=False)
    np.savez_compressed(_cache_path(), emb=np.asarray(emb, dtype="float32"))
    return np.asarray(emb, dtype="float32")


def search(query, docs, top=5):
    """Rank docs by embedding cosine similarity to the query.

    Returns a list of (stem, title, score) or [] when unavailable.
    """
    if not available():
        return []
    import numpy as np

    emb = encode_docs(docs)
    if emb is None:
        return []
    model = _load_model()
    q = model.encode([query], normalize_embeddings=True,
                     show_progress_bar=False)[0]
    scores = emb @ np.asarray(q, dtype="float32")
    order = np.argsort(-scores)[:top]
    return [(docs[i]["stem"], docs[i]["title"], round(float(scores[i]), 3))
            for i in order if scores[i] > 0]


def main(argv=None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="ml.embeddings")
    p.add_argument("query", nargs="?", default=None)
    p.add_argument("--top", type=int, default=5)
    args = p.parse_args(argv)

    if not available():
        print("Optional embeddings not installed. Install with:")
        print("  pip install sentence-transformers numpy")
        print("Until then, use the stdlib fallback: python3 -m ml.search")
        return 0
    sys.path.insert(0, str(ROOT))
    from ml.search import load_corpus

    docs = load_corpus()
    if args.query:
        for stem, title, score in search(args.query, docs, args.top):
            print(f"  {score:.2f} {stem} — {title}")
    else:
        print(f"Embeddings available ({MODEL_NAME}); "
              f"{len(docs)} docs indexed. Pass a query to search.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
