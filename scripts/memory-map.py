#!/usr/bin/env python3
"""scripts/memory-map.py — generate the full memory map (MEMORY-MAP.md).

The full memory map is the whole brain on one page: every file, its
tags, its wikilinks in and out, orphans, topic clusters (from the
ML step), sources, stale flags, and counts. It is GENERATED — never
edit MEMORY-MAP.md by hand.

What it covers (everything, not just notes/):
  notes/, wiki/, raw/, desk/, daily/, memory.md, index.md, log.md,
  rules/, skills/, templates/, ml/, scripts/, and the root docs
  (MUSE.md, README.md, MAP.md).

What it does:
  1. Runs the ML reports (clusters, link suggestions, duplicates,
     possible tensions) via ml/search.py — stdlib TF-IDF/BM25, so it
     works with no extra installs. Falls back to tag groups if the
     ML import fails for any reason.
  2. Renders MEMORY-MAP.md.
  3. Re-runs scan.py so MAP.md and dashboard.html match the same
     file set.

Usage (run from the repo root):
  python3 scripts/memory-map.py

Stale rule: a file whose content has not changed in 90+ days is
listed as a stale candidate for weekly review — a prompt, not a
verdict. Source rule: a note with "[source needed]" or no source
line at all is flagged until it names one.
"""
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import scan as scan_mod  # noqa: E402  (root scan.py: notes index + dashboard)

OUT_PATH = ROOT / "MEMORY-MAP.md"
STALE_DAYS = 90

# area -> (label, glob pattern, recursive?)
AREAS = [
    ("notes", "Notes — atomic layer", "notes", "*.md", False),
    ("wiki", "Wiki — compiled synthesis", "wiki", "*.md", False),
    ("raw", "Raw — immutable sources", "raw", "*", True),
    ("desk", "Desk — working surface", "desk", "*", True),
    ("daily", "Daily — day pages", "daily", "*.md", False),
    ("memory", "Memory", ".", "memory.md", False),
    ("index", "Index", ".", "index.md", False),
    ("log", "Log", ".", "log.md", False),
    ("rules", "Rules", "rules", "*.md", False),
    ("skills", "Skills", "skills", "SKILL.md", True),
    ("templates", "Templates", "templates", "*.md", False),
    ("ml", "ML — local-first", "ml", "*.py", False),
    ("scripts", "Scripts", "scripts", "*.py", False),
    ("root", "Root docs", ".", None, False),
]
ROOT_DOCS = ["MUSE.md", "README.md", "MAP.md", "MEMORY-MAP.md"]

TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
TAG_RE = re.compile(r"#([A-Za-z][A-Za-z0-9_-]*)")
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]]*)?(?:\|[^\]]*)?\]\]")
SOURCE_RE = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?Source:(?:\*\*)?\s+(.+?)\s*$", re.MULTILINE)
PER_SOURCE_RE = re.compile(r"\(per\s+([^,]+,\s*20\d\d[^)]*)\)")


def normalize_target(raw: str) -> str:
    return raw.strip().lower().replace(" ", "-")


def collect_files():
    """Every tracked file in the brain, grouped by area."""
    files = []  # dicts: rel, area, title, tags, links, sources, mtime
    seen = set()
    for area, _label, folder, pattern, recursive in AREAS:
        base = ROOT / folder if folder != "." else ROOT
        if pattern is None:  # root docs, listed explicitly
            for name in ROOT_DOCS:
                p = ROOT / name
                if p.exists() and str(p) not in seen:
                    seen.add(str(p))
                    files.append(_read_file(p, area))
            continue
        glob = base.rglob(pattern) if recursive else base.glob(pattern)
        for p in sorted(glob):
            if not p.is_file():
                continue
            if p.name == "README.md" and area == "wiki":
                # wiki/README.md is a folder readme, not a page.
                continue
            if str(p) in seen or p.name == "SCRUB-REPORT.md":
                continue
            if ".git" in p.parts:
                continue
            seen.add(str(p))
            files.append(_read_file(p, area))
    return files


def _read_file(path: Path, area: str):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        text = ""
    title_m = TITLE_RE.search(text)
    sources = SOURCE_RE.findall(text)
    # Most notes carry sources inline, at the end of a fact line —
    # "(per Akshith, Oct 2026)" or "(Source: ~/memory/…)". Those are
    # real source trails too; the line-anchored regex above misses
    # them, so collect them as well (same rule as scan.py).
    sources += [f"per {m}" for m in PER_SOURCE_RE.findall(text)]
    sources += re.findall(r"\(Source:\s*[^)]+\)", text)
    _seen = set()
    sources = [" ".join(str(x).split()) for x in sources]
    sources = [x for x in sources if not (x in _seen or _seen.add(x))][:3]
    # Links inside `inline code` are mentions/examples (e.g. `[[links]]`
    # in a skill doc), not real links — exclude them from the graph.
    link_text = re.sub(r"`[^`]*`", " ", text)
    links = sorted({normalize_target(t) for t in LINK_RE.findall(link_text)})
    if area == "templates":
        # Templates hold placeholder [[...]] examples, not real links.
        links = []
    return {
        "rel": str(path.relative_to(ROOT)),
        "area": area,
        "title": title_m.group(1) if title_m else path.stem,
        "tags": sorted(set(TAG_RE.findall(text))) if path.suffix == ".md" else [],
        "links": links,
        "sources": sources,
        "needs_source": "[source needed]" in text,
        "mtime": path.stat().st_mtime if path.exists() else 0,
        "text": text,
    }


def build_link_index(files):
    """Incoming links per stem across ALL markdown files."""
    stems = {Path(f["rel"]).stem for f in files if f["rel"].endswith(".md")}
    incoming = defaultdict(list)
    broken = []
    for f in files:
        if not f["rel"].endswith(".md"):
            continue
        for target in f["links"]:
            if target in stems:
                incoming[target].append(Path(f["rel"]).stem)
            else:
                broken.append((Path(f["rel"]).stem, target))
    return incoming, sorted(set(broken)), stems


def ml_reports():
    """Clusters / link suggestions / duplicates / tensions from ml/."""
    try:
        from ml.search import Index, load_corpus

        docs = load_corpus()
        if not docs:
            return {"clusters": [], "suggest_links": [],
                    "duplicates": [], "conflicts": [], "error": "no docs"}
        idx = Index(docs)
        return {
            "clusters": idx.clusters(),
            "suggest_links": [{"a": s["a"]["stem"], "b": s["b"]["stem"],
                               "cosine": s["cosine"],
                               "shared_tags": s["shared_tags"]}
                              for s in idx.suggest_links()],
            "duplicates": idx.duplicates(),
            "conflicts": idx.conflicts(),
            "error": None,
        }
    except Exception as exc:  # ML must never block the map
        return {"clusters": [], "suggest_links": [], "duplicates": [],
                "conflicts": [], "error": f"ML unavailable ({exc})"}


def _bar(n, cap=12):
    """Degree bar: one block per link, capped so tables stay readable."""
    n = max(0, int(n))
    return "█" * min(n, cap) + ("+" if n > cap else "")


def _mermaid_id(stem):
    return "n_" + re.sub(r"[^A-Za-z0-9_]", "_", stem)


def _mermaid_label(title, maxlen=24):
    t = str(title).replace('"', "'").replace("\n", " ").strip()
    return (t[:maxlen - 1] + "…") if len(t) > maxlen else t


def render(files, incoming, broken, ml, now_str, now_ts):
    total_notes = sum(1 for f in files if f["area"] == "notes")
    total_links = sum(len(f["links"]) for f in files if f["rel"].endswith(".md"))
    orphans = sorted(
        Path(f["rel"]).stem for f in files
        if f["area"] == "notes" and not f["links"]
        and not incoming.get(Path(f["rel"]).stem)
    )
    stale = sorted(
        f["rel"] for f in files
        if (now_ts - f["mtime"]) > STALE_DAYS * 86400
    )
    need_source = sorted(f["rel"] for f in files if f["needs_source"])
    no_source = sorted(
        f["rel"] for f in files
        if f["area"] in ("notes", "wiki", "memory") and not f["sources"]
        and not f["needs_source"]
    )
    tag_counts = Counter()
    for f in files:
        tag_counts.update(f["tags"])
    by_stem = {Path(f["rel"]).stem: f for f in files}
    notes = [f for f in files if f["area"] == "notes"]
    degree = {Path(f["rel"]).stem:
              len(f["links"]) + len(incoming.get(Path(f["rel"]).stem, []))
              for f in notes}
    hubs = sorted(notes,
                  key=lambda f: -degree[Path(f["rel"]).stem])[:8]
    # Cluster membership (ML order = colour rank in docs/design-system.md).
    clusters = ml.get("clusters") or []
    cluster_of = {}
    for ci, c in enumerate(clusters):
        for m in c.get("members", []):
            cluster_of[m] = ci
    cluster_colors = ["#7C5CFF", "#14B8A6", "#F59E0B", "#F43F5E",
                      "#0EA5E9", "#10B981", "#F97316", "#6366F1"]

    L = []
    L.append("# ◈ MEMORY-MAP — the full memory map of the brain")
    L.append("")
    L.append(f"_Generated by `scripts/memory-map.py` on {now_str}. "
             "Do not edit by hand — re-run "
             "`python3 scripts/memory-map.py`._")
    L.append("")
    L.append("> **How to read this map.** Every node is a real note; every "
             "edge is a real `[[wiki-link]]`; every colour is a real ML "
             "topic cluster. Big nodes are hubs — the notes everything "
             "else hangs off. Dashed, quiet notes have no links yet: "
             "invitations, not errors. Start with the hubs, then follow "
             "a cluster.")
    L.append("")
    L.append("## At a glance")
    L.append("")
    wiki_n = sum(1 for f in files if f["area"] == "wiki")
    L.append("| Notes | Links | Clusters | Hubs | Quiet notes | Duplicates |")
    L.append("| ---: | ---: | ---: | ---: | ---: | ---: |")
    L.append(f"| **{total_notes}** | **{total_links}** | "
             f"**{len(clusters)}** | **{len(hubs)}** | "
             f"**{len(orphans)}** | **{len(ml.get('duplicates') or [])}** |")
    L.append("")
    L.append(f"- Files mapped: **{len(files)}** "
             f"({total_notes} notes, "
             f"{wiki_n} wiki {'page' if wiki_n == 1 else 'pages'})")
    L.append(f"- Wikilinks: **{total_links}** "
             f"({sum(len(v) for v in incoming.values())} resolved, "
             f"{len(broken)} broken)")
    L.append(f"- Link suggestions (ML): **{len(ml.get('suggest_links') or [])}**")
    L.append(f"- Possible tensions (heuristic): **{len(ml.get('conflicts') or [])}**")
    L.append(f"- Stale candidates (unchanged 90+ days): **{len(stale)}**")
    L.append(f"- Pages marked `[source needed]`: **{len(need_source)}**")
    L.append(f"- Notes/wiki/memory pages with no source line: "
             f"**{len(no_source)}**")
    L.append("")
    if ml.get("error"):
        L.append(f"> ML reports unavailable this run: {ml['error']} "
                 "Clusters below fall back to tag groups.")
        L.append("")

    # ---- What Muse knows (the digital copy, after sign-in) ----
    # Same data the dashboard's "What Muse knows" view shows: topics
    # by area, each with its one-line summary and source trail. See
    # docs/login.md. Generated from the real files — no invented facts.
    L.append("## What Muse knows — the digital copy")
    L.append("")
    L.append("> Sign in (see `docs/login.md`) and this is the view you "
             "get: your information as an interactive memory map. Every "
             "topic below is a real note; every source is a real line in "
             "that note. Where Muse has no source, it says so — check "
             "the trail before you trust the summary.")
    L.append("")
    _knows_areas = {}
    for f in notes:
        tag = (f["tags"] or ["notes"])[0]
        _knows_areas.setdefault(tag, []).append(f)
    for tag in sorted(_knows_areas, key=lambda t: -len(_knows_areas[t])):
        members = sorted(_knows_areas[tag],
                         key=lambda f: -degree[Path(f["rel"]).stem])
        with_src = sum(1 for f in members if f["sources"])
        L.append(f"- **{tag.title()}** — {len(members)} note"
                 f"{'s' if len(members) != 1 else ''} "
                 f"({with_src} with a source trail): " +
                 ", ".join(f"`[[{Path(f['rel']).stem}]]`" for f in members[:5]) +
                 (" \u2026" if len(members) > 5 else ""))
    L.append("")
    for f in sorted(notes, key=lambda f: -degree[Path(f["rel"]).stem])[:8]:
        stem = Path(f["rel"]).stem
        _txt = f["text"]
        _para, _started = [], False
        for ln in _txt.split("\n"):
            ln = ln.strip()
            if not ln:
                if _started:
                    break
                continue
            if ln.startswith("#") or ln.startswith("Tags:") or ln.startswith(">"):
                continue
            _started = True
            _para.append(ln)
        _excerpt = " ".join(_para)
        if len(_excerpt) > 180:
            _excerpt = _excerpt[:177] + "\u2026"
        _excerpt = _excerpt.replace("[[", "").replace("]]", "")
        L.append(f"- **`[[{stem}]]`** — {_excerpt}")
        if f["sources"]:
            L.append(f"  - Sources: " + "; ".join(f["sources"][:3]))
        else:
            L.append("  - Sources: _none on file — check before trusting_")
    L.append("")
    L.append(f"_Coverage: **{len([f for f in notes if f['sources']])}/{total_notes}** "
             "notes carry a source trail; "
             f"**{len(need_source)}** marked `[source needed]`; "
             f"**{len(no_source)}** pages with no source line at all._")
    L.append("")

    # ---- Hubs ----
    L.append("## Hubs — the most-connected notes")
    L.append("")
    L.append("| Note | Links | Degree |")
    L.append("| --- | ---: | --- |")
    for f in hubs:
        stem = Path(f["rel"]).stem
        L.append(f"| `[[{stem}]]` | {degree[stem]} | {_bar(degree[stem])} |")
    L.append("")
    L.append("_Read a hub first when you come back to the brain — it "
             "re-orients you faster than any index._")
    L.append("")

    # ---- Clusters as cards ----
    L.append("## Clusters — where the brain actually lives")
    L.append("")
    if clusters:
        for ci, c in enumerate(clusters):
            members = c.get("members", [])
            color = cluster_colors[ci % len(cluster_colors)]
            bar = _bar(len(members), cap=24)
            L.append(f"### {ci + 1}. <span style=\"color:{color}\">●</span> "
                     f"**{c['label']}** — {len(members)} note"
                     f"{'s' if len(members) != 1 else ''}")
            L.append("")
            L.append(f"`{bar}` {len(members)}/{total_notes} notes")
            L.append("")
            L.append(", ".join(f"`[[{m}]]`" for m in members))
            L.append("")
    else:
        by_tag = defaultdict(list)
        for f in files:
            for t in f["tags"]:
                by_tag[t].append(Path(f["rel"]).stem)
        for tag in sorted(by_tag):
            L.append(f"- **#{tag}** ({len(by_tag[tag])}): "
                     f"{', '.join(sorted(by_tag[tag]))}")
        L.append("")

    # ---- Mermaid diagram ----
    L.append("## The map — as a diagram")
    L.append("")
    L.append("Rendered by GitHub from the real links below. "
             "Every node is a note; every edge is a `[[wiki-link]]`.")
    L.append("")
    # Edges: all intra-cluster edges, plus cross-cluster edges that
    # touch a hub — capped at 48 so the diagram stays readable.
    hub_stems = {Path(f["rel"]).stem for f in hubs}
    edges = []
    seen_edges = set()
    for f in notes:
        a = Path(f["rel"]).stem
        for t in f["links"]:
            if t not in by_stem or t == a:
                continue
            key = tuple(sorted((a, t)))
            if key in seen_edges:
                continue
            seen_edges.add(key)
            same_cluster = (cluster_of.get(a) is not None
                            and cluster_of.get(a) == cluster_of.get(t))
            if same_cluster or a in hub_stems or t in hub_stems:
                edges.append((a, t))
    edges = edges[:48]
    shown = {s for e in edges for s in e}
    # Nodes in clusters with no shown edge still appear, unlinked.
    for m in cluster_of:
        shown.add(m)
    L.append("```mermaid")
    L.append("flowchart LR")
    for ci, c in enumerate(clusters):
        members = [m for m in c.get("members", []) if m in shown]
        if not members:
            continue
        L.append(f"    subgraph c{ci}[\"{c['label']}\"]")
        for m in members:
            f = by_stem.get(m)
            title = f["title"] if f else m
            L.append(f"        {_mermaid_id(m)}[\"{_mermaid_label(title)}\"]")
        L.append("    end")
    # Singleton notes (no cluster) get their own nodes.
    for m in sorted(shown):
        if m not in cluster_of:
            f = by_stem.get(m)
            title = f["title"] if f else m
            L.append(f"    {_mermaid_id(m)}[\"{_mermaid_label(title)}\"]")
    for a, b in edges:
        L.append(f"    {_mermaid_id(a)} --> {_mermaid_id(b)}")
    L.append("```")
    L.append("")
    total_edges = len(seen_edges)
    L.append(f"_{len(edges)} of {total_edges} links shown — "
             "intra-cluster links and links touching a hub. "
             "The full list is in **Every file** below._")
    L.append("")

    # ---- Link suggestions / tensions ----
    L.append("## Link suggestions — unlinked pairs worth linking")
    L.append("")
    if ml.get("suggest_links"):
        for s in (ml["suggest_links"] or [])[:20]:
            tags = (f" shared tags: {', '.join(s['shared_tags'])}"
                    if s.get("shared_tags") else "")
            L.append(f"- {s['cosine']:.2f} `[[{s['a']}]]` ↔ "
                     f"`[[{s['b']}]]`{tags}")
    else:
        L.append("- None — every similar pair is already linked.")
    L.append("")
    if ml.get("duplicates"):
        L.append("## Duplicates flagged")
        L.append("")
        for d in ml["duplicates"]:
            L.append(f"- {d['kind']} {d['score']:.2f}: "
                     f"`{d['a']}` ~ `{d['b']}`")
        L.append("")
    if ml.get("conflicts"):
        L.append("## Possible tensions — review by hand, never auto-fix")
        L.append("")
        for c in ml["conflicts"]:
            L.append(f"- {c['cosine']:.2f} `{c['a']}` ~ `{c['b']}`: {c['note']}")
        L.append("")

    # ---- Quiet notes / attention ----
    L.append("## Quiet notes — no links yet, invitations not errors")
    L.append("")
    if orphans:
        for stem in orphans:
            f = by_stem.get(stem)
            title = f["title"] if f else stem
            L.append(f"- `[[{stem}]]` — {title}. "
                     "Link it to one hub and it joins the map.")
    else:
        L.append("- None — every note is linked in.")
    L.append("")
    if broken:
        L.append("## Broken links")
        L.append("")
        for src, target in broken:
            L.append(f"- `{src}` links to `[[{target}]]` — no such note")
        L.append("")
    if stale:
        L.append("## Stale candidates — unchanged 90+ days, review don't delete")
        L.append("")
        for rel in stale:
            L.append(f"- `{rel}`")
        L.append("")

    # ---- Every file, grouped by cluster ----
    L.append("## Every file — grouped by cluster")
    L.append("")
    L.append("| File | Title | Tags | Out | In | Degree | Sources | Flags |")
    L.append("| --- | --- | --- | ---: | ---: | ---: | --- | --- |")

    def _cell(s):
        return re.sub(r"[`|\n\r]", " ", str(s)).strip()

    def _row(f):
        stem = Path(f["rel"]).stem
        flags = []
        if stem in orphans:
            flags.append("quiet")
        if f["rel"] in stale:
            flags.append("stale?")
        if f["needs_source"]:
            flags.append("source needed")
        elif f["area"] in ("notes", "wiki", "memory") and not f["sources"]:
            flags.append("no source line")
        src = "; ".join(f["sources"][:1])
        deg = degree.get(stem, len(f["links"]) +
                         len(incoming.get(stem, [])))
        return (f"| `{f['rel']}` | {_cell(f['title'])} | "
                f"{' '.join('#' + t for t in f['tags'])} | "
                f"{len(f['links'])} | {len(incoming.get(stem, []))} | "
                f"{_bar(deg)} {deg} | {_cell(src)} | {', '.join(flags)} |")

    for ci, c in enumerate(clusters):
        members = [by_stem[m] for m in c.get("members", []) if m in by_stem]
        if not members:
            continue
        L.append("")
        L.append(f"### Cluster {ci + 1} — {c['label']}")
        L.append("")
        for f in sorted(members, key=lambda x: x["rel"]):
            L.append(_row(f))
    rest = [f for f in files
            if Path(f["rel"]).stem not in cluster_of]
    if rest:
        L.append("")
        L.append("### System files — the map's own machinery")
        L.append("")
        for f in sorted(rest, key=lambda x: (x["area"], x["rel"])):
            L.append(_row(f))
    L.append("")

    if need_source or no_source:
        L.append("## Source gaps")
        L.append("")
        for rel in need_source:
            L.append(f"- `{rel}` — marked `[source needed]`")
        for rel in no_source:
            L.append(f"- `{rel}` — no source line found")
        L.append("")
    return "\n".join(L)

def main() -> int:
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%d %H:%M UTC")
    files = collect_files()
    incoming, broken, _stems = build_link_index(files)
    ml = ml_reports()
    OUT_PATH.write_text(
        render(files, incoming, broken, ml, now_str, now.timestamp()),
        encoding="utf-8",
    )
    print(f"Mapped {len(files)} files, "
          f"{sum(len(f['links']) for f in files if f['rel'].endswith('.md'))} links.")
    print(f"Clusters: {len(ml['clusters'])}; "
          f"link suggestions: {len(ml['suggest_links'])}; "
          f"duplicates: {len(ml['duplicates'])}; "
          f"tensions: {len(ml['conflicts'])}.")
    if ml["error"]:
        print(f"ML note: {ml['error']}")
    print(f"Wrote {OUT_PATH.name}.")
    # Keep MAP.md + dashboard.html in sync with the same file set.
    rc = scan_mod.main()
    if rc != 0:
        print("scan.py failed after writing MEMORY-MAP.md", file=sys.stderr)
        return rc
    print("Regenerated MAP.md and dashboard.html via scan.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
