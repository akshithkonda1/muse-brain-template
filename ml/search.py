#!/usr/bin/env python3
"""ml/search.py — local-first ML search for Muse Brain. Stdlib only.

Baseline (always available, zero extra deps):
  TF-IDF cosine ranking + BM25 ranking over notes/ and wiki/.
  Related-note ranking, link suggestions, topic clustering, and
  upgraded duplicate / tension detection built on the same text.

Optional (graceful fallback): if `sentence-transformers` + `numpy`
are installed, `ml/embeddings.py` adds local embedding search on
top of the same corpus. If they are absent, everything below still
works — this module never imports them and never calls any API.

Privacy: everything runs on this machine, on files already in the
repo. No network calls, no API keys, no telemetry, no daemon.
Generated embedding caches live in ml/.cache/ (gitignored) and are
never committed.

Usage (run from the repo root):
  python3 -m ml.search "query"        # ranked search (BM25 + TF-IDF)
  python3 -m ml.search --related <stem>   # notes most related to one note
  python3 -m ml.search --suggest-links   # unlinked pairs worth linking
  python3 -m ml.search --clusters        # topic clusters
  python3 -m ml.search --duplicates      # exact / Jaccard / semantic dups
  python3 -m ml.search --conflicts       # possible tensions (heuristic)
  python3 -m ml.search --all             # every report, for the map
  python3 -m ml.search --json "query"    # machine-readable output
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = [ROOT / "notes", ROOT / "wiki"]

STOP = set(
    "a an the and or of to in on for with is are was were be by at as it its "
    "this that these those from into over under after before not no nor but "
    "if then than so such can could will would should he she they we you i "
    "his her their our your my me him them us what which who whom when where "
    "why how all any both each few more most other some such only own same "
    "too very just also".split()
)
NEGATION_MARKERS = {
    "not", "never", "no", "out", "dropped", "cancelled", "canceled",
    "versus", "vs", "instead", "tension", "conflict", "contradicts",
}
TOKEN_RE = re.compile(r"[a-z0-9']+")
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]]*)?(?:\|[^\]]*)?\]\]")
TAG_RE = re.compile(r"#([A-Za-z][A-Za-z0-9_-]*)")
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def clean_text(text: str) -> str:
    """Strip code fences / markdown markup; expand [[links]] to words."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = LINK_RE.sub(lambda m: " " + m.group(1).replace("-", " ") + " ", text)
    text = re.sub(r"[#*`>\[\]()|_]", " ", text)
    return text


def tokenize(text: str):
    return [w for w in TOKEN_RE.findall(clean_text(text).lower())
            if w not in STOP and len(w) > 1]


def load_corpus():
    """Return list of docs: stem, file, title, tags, links, tokens, text."""
    docs = []
    for folder in FOLDERS:
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            if path.name == "README.md":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            title_m = TITLE_RE.search(text)
            docs.append({
                "stem": path.stem,
                "file": str(path.relative_to(ROOT)),
                "title": title_m.group(1) if title_m else path.stem,
                "tags": sorted(set(TAG_RE.findall(text))),
                "links": sorted({l.strip().lower().replace(" ", "-")
                                 for l in LINK_RE.findall(text)}),
                "tokens": tokenize(text),
                "text": text,
            })
    return docs


class Index:
    """TF-IDF vectors + BM25 over a small Markdown corpus."""

    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = docs
        self.k1 = k1
        self.b = b
        self.n = len(docs)
        self.df = Counter()
        self.doc_len = []
        for d in docs:
            counts = Counter(d["tokens"])
            d["counts"] = counts
            self.doc_len.append(sum(counts.values()))
            for term in counts:
                self.df[term] += 1
        self.avgdl = (sum(self.doc_len) / self.n) if self.n else 0.0
        # Smoothed IDF (BM25-style, never negative).
        self.idf = {t: math.log((self.n - df + 0.5) / (df + 0.5) + 1)
                    for t, df in self.df.items()}
        for d in docs:
            vec = {}
            for term, tf in d["counts"].items():
                vec[term] = (1 + math.log(tf)) * self.idf.get(term, 0.0)
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            d["tfidf"] = {t: v / norm for t, v in vec.items()}

    def _query_vec(self, query):
        counts = Counter(tokenize(query))
        vec = {}
        for term, tf in counts.items():
            if term in self.idf:
                vec[term] = (1 + math.log(tf)) * self.idf[term]
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def cosine(self, a, b):
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(t, 0.0) for t, v in a.items())

    def bm25(self, query_terms):
        scores = []
        for i, d in enumerate(self.docs):
            score = 0.0
            dl = self.doc_len[i] or 1
            for term in query_terms:
                tf = d["counts"].get(term, 0)
                if not tf:
                    continue
                idf = self.idf.get(term, 0.0)
                denom = tf + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
                score += idf * tf * (self.k1 + 1) / denom
            scores.append(score)
        return scores

    def search(self, query, top=5):
        """Ranked search: BM25 primary, TF-IDF cosine as the second signal."""
        qvec = self._query_vec(query)
        qterms = [t for t in Counter(tokenize(query)) if t in self.idf]
        bm25 = self.bm25(qterms)
        out = []
        for i, d in enumerate(self.docs):
            cos = self.cosine(qvec, d["tfidf"])
            out.append({"doc": d, "bm25": round(bm25[i], 3),
                        "cosine": round(cos, 3),
                        "score": round(bm25[i] + cos, 3)})
        out.sort(key=lambda r: r["score"], reverse=True)
        return [r for r in out if r["score"] > 0][:top]

    def related(self, stem, top=5):
        """Notes most similar to one note (TF-IDF cosine)."""
        target = next((d for d in self.docs if d["stem"] == stem), None)
        if target is None:
            return []
        out = []
        for d in self.docs:
            if d is target:
                continue
            out.append({"doc": d,
                        "cosine": round(self.cosine(target["tfidf"], d["tfidf"]), 3)})
        out.sort(key=lambda r: r["cosine"], reverse=True)
        return [r for r in out if r["cosine"] > 0][:top]

    def suggest_links(self, threshold=0.20):
        """Unlinked pairs worth linking, by TF-IDF cosine."""
        suggestions = []
        for i, a in enumerate(self.docs):
            for b in self.docs[i + 1:]:
                if b["stem"] in a["links"] or a["stem"] in b["links"]:
                    continue
                cos = self.cosine(a["tfidf"], b["tfidf"])
                if cos >= threshold:
                    shared = sorted(set(a["tags"]) & set(b["tags"]))
                    suggestions.append({"a": a, "b": b,
                                        "cosine": round(cos, 3),
                                        "shared_tags": shared})
        suggestions.sort(key=lambda s: s["cosine"], reverse=True)
        return suggestions

    def clusters(self, threshold=0.15):
        """Greedy agglomerative clustering on TF-IDF cosine.

        Small corpora, simple rule: a doc joins the cluster it is most
        similar to (if above threshold), else it starts a new one.
        Labels are the cluster's top TF-IDF terms.
        """
        clusters = []  # list of list-of-docs
        for d in self.docs:
            best, best_cos = None, 0.0
            for c in clusters:
                cos = max(self.cosine(d["tfidf"], m["tfidf"]) for m in c)
                if cos > best_cos:
                    best, best_cos = c, cos
            if best is not None and best_cos >= threshold:
                best.append(d)
            else:
                clusters.append([d])
        out = []
        for c in clusters:
            agg = Counter()
            for d in c:
                for term, weight in d["tfidf"].items():
                    agg[term] += weight
            label = ", ".join(t for t, _ in agg.most_common(3))
            out.append({"label": label or "(no terms)",
                        "members": [d["stem"] for d in c]})
        out.sort(key=lambda c: len(c["members"]), reverse=True)
        return out

    def duplicates(self, jaccard_threshold=0.72, cosine_threshold=0.85):
        """Exact (SHA-256) + Jaccard + semantic (TF-IDF cosine) duplicates.

        Reuses the dup-check.py rule and adds the cosine check, which
        catches near-duplicates that reword the same content.
        """
        import hashlib

        def word_set(d):
            return {w for w in TOKEN_RE.findall(clean_text(d["text"]).lower())
                    if w not in STOP}

        found = []
        for i, a in enumerate(self.docs):
            for b in self.docs[i + 1:]:
                if a["text"] == b["text"]:
                    found.append({"a": a["stem"], "b": b["stem"],
                                  "kind": "exact", "score": 1.0})
                    continue
                wa, wb = word_set(a), word_set(b)
                jac = len(wa & wb) / len(wa | wb) if (wa | wb) else 0.0
                cos = self.cosine(a["tfidf"], b["tfidf"])
                if jac > jaccard_threshold:
                    found.append({"a": a["stem"], "b": b["stem"],
                                  "kind": "likely-duplicate (Jaccard)",
                                  "score": round(jac, 3)})
                elif cos > cosine_threshold:
                    found.append({"a": a["stem"], "b": b["stem"],
                                  "kind": "near-duplicate (semantic)",
                                  "score": round(cos, 3)})
        return found

    def conflicts(self, cosine_threshold=0.45):
        """Possible tensions: similar docs whose tags don't overlap and
        where one side carries a negation / reversal marker.

        This is a heuristic flag for human review, never a verdict:
        two notes can legitimately cover the same topic from two sides.
        """
        found = []
        for i, a in enumerate(self.docs):
            for b in self.docs[i + 1:]:
                cos = self.cosine(a["tfidf"], b["tfidf"])
                if cos < cosine_threshold:
                    continue
                if set(a["tags"]) & set(b["tags"]):
                    continue
                a_neg = bool(NEGATION_MARKERS & set(tokenize(a["text"])))
                b_neg = bool(NEGATION_MARKERS & set(tokenize(b["text"])))
                if a_neg or b_neg:
                    found.append({"a": a["stem"], "b": b["stem"],
                                  "cosine": round(cos, 3),
                                  "note": "similar topic, disjoint tags, "
                                          "negation marker present — review"})
        return found


def _doc_line(d):
    return f"{d['stem']} — {d['title']} ({d['file']})"


def main(argv=None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="ml.search",
                                description="Local-first ML search for Muse Brain.")
    p.add_argument("query", nargs="?", default=None,
                   help="search query (default mode: ranked search)")
    p.add_argument("--related", metavar="STEM",
                   help="notes most related to this note stem")
    p.add_argument("--suggest-links", action="store_true",
                   help="unlinked pairs worth linking")
    p.add_argument("--clusters", action="store_true",
                   help="topic clusters")
    p.add_argument("--duplicates", action="store_true",
                   help="exact / Jaccard / semantic duplicates")
    p.add_argument("--conflicts", action="store_true",
                   help="possible tensions (heuristic)")
    p.add_argument("--all", action="store_true",
                   help="every report (for MEMORY-MAP.md)")
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    docs = load_corpus()
    if not docs:
        print("No notes found in notes/ or wiki/.", file=sys.stderr)
        return 1
    idx = Index(docs)

    result = {}
    if args.related:
        result["related"] = [{"stem": r["doc"]["stem"],
                              "title": r["doc"]["title"],
                              "cosine": r["cosine"]}
                             for r in idx.related(args.related, args.top)]
    if args.suggest_links or args.all:
        result["suggest_links"] = [
            {"a": s["a"]["stem"], "b": s["b"]["stem"],
             "cosine": s["cosine"], "shared_tags": s["shared_tags"]}
            for s in idx.suggest_links()]
    if args.clusters or args.all:
        result["clusters"] = idx.clusters()
    if args.duplicates or args.all:
        result["duplicates"] = idx.duplicates()
    if args.conflicts or args.all:
        result["conflicts"] = idx.conflicts()
    if args.query is not None:
        result["search"] = [
            {"stem": r["doc"]["stem"], "title": r["doc"]["title"],
             "bm25": r["bm25"], "cosine": r["cosine"], "score": r["score"]}
            for r in idx.search(args.query, args.top)]

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    if "search" in result:
        print(f"Search: {args.query!r} ({len(docs)} docs)")
        for r in result["search"]:
            print(f"  {r['score']:.2f} (BM25 {r['bm25']:.2f}, cos {r['cosine']:.2f}) "
                  f"{r['stem']} — {r['title']}")
        if not result["search"]:
            print("  (no matches — try fewer / different words)")
    if "related" in result:
        print(f"Related to {args.related}:")
        for r in result["related"]:
            print(f"  {r['cosine']:.2f} {r['stem']} — {r['title']}")
        if not result["related"]:
            print("  (no related notes found)")
    if "suggest_links" in result:
        print(f"Link suggestions ({len(result['suggest_links'])}):")
        for s in result["suggest_links"][:15]:
            tags = f" shared tags: {', '.join(s['shared_tags'])}" if s["shared_tags"] else ""
            print(f"  {s['cosine']:.2f} [[{s['a']}]] <-> [[{s['b']}]]{tags}")
    if "clusters" in result:
        print(f"Clusters ({len(result['clusters'])}):")
        for c in result["clusters"]:
            print(f"  [{c['label']}] ({len(c['members'])}) "
                  f"{', '.join(c['members'])}")
    if "duplicates" in result:
        print(f"Duplicates ({len(result['duplicates'])}):")
        for d in result["duplicates"]:
            print(f"  {d['kind']} {d['score']:.2f}: {d['a']} ~ {d['b']}")
        if not result["duplicates"]:
            print("  none")
    if "conflicts" in result:
        print(f"Possible tensions ({len(result['conflicts'])} — heuristic, review by hand):")
        for c in result["conflicts"]:
            print(f"  {c['cosine']:.2f} {c['a']} ~ {c['b']}: {c['note']}")
        if not result["conflicts"]:
            print("  none")
    if not result:
        p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
