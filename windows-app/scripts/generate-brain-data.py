#!/usr/bin/env python3
"""Generate the React Native Windows app's bundled brain snapshot.

Reads the Markdown brain (the source of truth) with the repo's own
scan.py + ml/search.py and writes windows-app/src/brain-data.json:
every note's full text, tags, links, precomputed graph positions,
clusters, link suggestions, orphans, stale flags, duplicates.

This is a *generated snapshot*, like dashboard.html's embedded data:
the Markdown files stay the source of truth — re-run this script
after editing notes, before building the .exe:

    python3 windows-app/scripts/generate-brain-data.py
    # or: npm run brain-data   (from windows-app/)

The JSON is committed (it is the app's data payload) — but it must
never contain anything the repo itself doesn't contain. For the
public template it holds only the example notes.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml"))

import scan  # noqa: E402
from search import Index, load_corpus  # noqa: E402

OUT = ROOT / "windows-app" / "src" / "brain-data.json"


def main() -> int:
    docs = load_corpus()
    notes = scan.scan_notes()
    # Graph + layout over the FULL corpus (notes/ + wiki/), so every
    # note in the app gets a graph position — scan_notes() alone is
    # notes/ only and would leave wiki pages position-less.
    incoming, broken, orphans = scan.build_graph(docs)
    idx = Index(docs)
    clusters = idx.clusters()
    positions = scan.layout_positions(docs, incoming, clusters)

    stale_cutoff = datetime.now(timezone.utc).timestamp() - 90 * 86400
    # suggest_links() returns full doc dicts (Index mutates them in
    # place with counts/tfidf vectors). The app only needs stems —
    # serialize those, never the vectors (they bloat the bundle and
    # don't match the app's SuggestionData shape).
    def _stem(x):
        return x["stem"] if isinstance(x, dict) else x
    data = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "source": "Markdown brain (notes/ + wiki/) via scan.py + ml/search.py",
        "notes": [
            {
                "stem": d["stem"],
                "title": d["title"],
                "tags": d["tags"],
                "links": d["links"],
                "text": d["text"],
                "area": d["file"].split("/")[0],
                "mtime": next(
                    (n["mtime"] for n in notes if n["stem"] == d["stem"]), 0),
                "incoming": sorted(incoming.get(d["stem"], [])),
            }
            for d in docs
        ],
        "positions": positions,
        "clusters": [
            {"label": c["label"], "members": c["members"]}
            for c in clusters
        ],
        # Design system (docs/design-system.md): cluster colours by
        # cluster rank, largest first; node colour is its cluster colour.
        "clusterColors": ["#7C5CFF", "#14B8A6", "#F59E0B", "#F43F5E",
                          "#0EA5E9", "#10B981", "#F97316", "#6366F1"],
        "clusterIndex": {m: ci for ci, c in enumerate(clusters)
                         for m in c.get("members", [])},
        "hubs": sorted(
            ({"stem": d["stem"], "title": d["title"],
              "degree": len(d["links"]) + len(incoming.get(d["stem"], []))}
             for d in docs),
            key=lambda h: -h["degree"])[:8],
        "suggestions": [
            {"a": _stem(s["a"]), "b": _stem(s["b"]), "cosine": round(s["cosine"], 3),
             "shared_tags": s["shared_tags"]}
            for s in idx.suggest_links()
        ],
        "orphans": sorted(orphans),
        "broken": [[a, b] for a, b in broken],
        "stale": sorted(
            n["stem"] for n in notes if n["mtime"] < stale_cutoff),
        "duplicates": [
            {"a": d["a"], "b": d["b"], "kind": d["kind"],
             "score": round(d["score"], 3)}
            for d in idx.duplicates()
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False),
                   encoding="utf-8")
    print(f"wrote {OUT} — {len(docs)} notes, "
          f"{len(data['clusters'])} clusters, "
          f"{len(data['suggestions'])} link suggestions, "
          f"{len(orphans)} orphans")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
