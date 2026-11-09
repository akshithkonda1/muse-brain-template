#!/usr/bin/env python3
"""scripts/memory-map.py — generate the full memory map (MEMORY-MAP.md).

The full memory map is the whole brain on one page: every file, its
tags, its wikilinks in and out, orphans, topic clusters (from the
ML step), sources, stale flags, and counts. It is GENERATED — never
edit MEMORY-MAP.md by hand.

What it covers (everything, not just notes/):
  notes/, wiki/, raw/, desk/, daily/, memory.md, index.md, log.md,
  rules/, skills/, templates/, ml/, scripts/, and the root docs
  (MUSE.md, CLAUDE.md when present, README.md, MAP.md).

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
ROOT_DOCS = ["MUSE.md", "CLAUDE.md", "README.md", "MAP.md", "MEMORY-MAP.md"]

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
    sources = SOURCE_RE.findall(text)[:3]
    if not sources:
        sources = [f"per {m}" for m in PER_SOURCE_RE.findall(text)[:3]]
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

    L = []
    L.append("# MEMORY-MAP — full memory map of the brain")
    L.append("")
    L.append(f"_Generated by `scripts/memory-map.py` on {now_str}. "
             "Do not edit by hand — re-run "
             "`python3 scripts/memory-map.py`._")
    L.append("")
    L.append("## Stats")
    L.append("")
    wiki_n = sum(1 for f in files if f["area"] == "wiki")
    L.append(f"- Files mapped: **{len(files)}** "
             f"({total_notes} notes, "
             f"{wiki_n} wiki {'page' if wiki_n == 1 else 'pages'})")
    L.append(f"- Wikilinks: **{total_links}** "
             f"({sum(len(v) for v in incoming.values())} resolved, "
             f"{len(broken)} broken)")
    L.append(f"- Orphans (notes, no links in or out): **{len(orphans)}**")
    L.append(f"- Topic clusters (ML): **{len(ml['clusters'])}**")
    L.append(f"- Link suggestions (ML): **{len(ml['suggest_links'])}**")
    L.append(f"- Duplicates flagged: **{len(ml['duplicates'])}**")
    L.append(f"- Possible tensions (heuristic): **{len(ml['conflicts'])}**")
    L.append(f"- Stale candidates (unchanged 90+ days): **{len(stale)}**")
    L.append(f"- Pages marked `[source needed]`: **{len(need_source)}**")
    L.append(f"- Notes/wiki/memory pages with no source line: "
             f"**{len(no_source)}**")
    L.append("")
    L.append("## Files by area")
    L.append("")
    L.append("| Area | Files |")
    L.append("| --- | ---: |")
    for area, label, *_ in AREAS:
        n = sum(1 for f in files if f["area"] == area)
        if n:
            L.append(f"| {label} (`{area}/`) | {n} |")
    L.append("")

    if ml["error"]:
        L.append(f"> ML reports unavailable this run: {ml['error']} "
                 "Clusters below fall back to tag groups.")
        L.append("")

    L.append("## Topic clusters (ML, TF-IDF cosine)")
    L.append("")
    if ml["clusters"]:
        for c in ml["clusters"]:
            L.append(f"- **{c['label']}** ({len(c['members'])}): "
                     f"{', '.join(c['members'])}")
    else:
        by_tag = defaultdict(list)
        for f in files:
            for t in f["tags"]:
                by_tag[t].append(Path(f["rel"]).stem)
        for tag in sorted(by_tag):
            L.append(f"- **#{tag}** ({len(by_tag[tag])}): "
                     f"{', '.join(sorted(by_tag[tag]))}")
    L.append("")

    L.append("## Link suggestions (ML — unlinked pairs worth linking)")
    L.append("")
    if ml["suggest_links"]:
        for s in ml["suggest_links"][:20]:
            tags = (f" shared tags: {', '.join(s['shared_tags'])}"
                    if s["shared_tags"] else "")
            L.append(f"- {s['cosine']:.2f} `[[{s['a']}]]` ↔ "
                     f"`[[{s['b']}]]`{tags}")
    else:
        L.append("- None — every similar pair is already linked.")
    L.append("")

    if ml["duplicates"]:
        L.append("## Duplicates flagged")
        L.append("")
        for d in ml["duplicates"]:
            L.append(f"- {d['kind']} {d['score']:.2f}: "
                     f"`{d['a']}` ~ `{d['b']}`")
        L.append("")
    if ml["conflicts"]:
        L.append("## Possible tensions (heuristic — review by hand)")
        L.append("")
        for c in ml["conflicts"]:
            L.append(f"- {c['cosine']:.2f} `{c['a']}` ~ `{c['b']}`: {c['note']}")
        L.append("")

    L.append("## Every file")
    L.append("")
    L.append("| File | Title | Tags | Links out | Links in | Sources | Flags |")
    L.append("| --- | --- | --- | ---: | ---: | --- | --- |")
    for f in sorted(files, key=lambda x: (x["area"], x["rel"])):
        stem = Path(f["rel"]).stem
        flags = []
        if stem in orphans:
            flags.append("orphan")
        if f["rel"] in stale:
            flags.append("stale?")
        if f["needs_source"]:
            flags.append("source needed")
        elif f["area"] in ("notes", "wiki", "memory") and not f["sources"]:
            flags.append("no source line")
        # Table cells must not contain backticks, pipes, or newlines:
        # one stray backtick unbalances the next run's link parsing.
        def _cell(s):
            return re.sub(r"[`|\n\r]", " ", str(s)).strip()
        src = "; ".join(f["sources"][:1])
        L.append(f"| `{f['rel']}` | {_cell(f['title'])} | "
                 f"{' '.join('#' + t for t in f['tags'])} | "
                 f"{len(f['links'])} | {len(incoming.get(stem, []))} | "
                 f"{_cell(src)} | {', '.join(flags)} |")
    L.append("")

    if orphans:
        L.append("## Orphans")
        L.append("")
        for stem in orphans:
            L.append(f"- `{stem}`")
        L.append("")
    if broken:
        L.append("## Broken links")
        L.append("")
        for src, target in broken:
            L.append(f"- `{src}` links to `[[{target}]]` — no such note")
        L.append("")
    if stale:
        L.append("## Stale candidates (unchanged 90+ days — review, don't delete)")
        L.append("")
        for rel in stale:
            L.append(f"- `{rel}`")
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
