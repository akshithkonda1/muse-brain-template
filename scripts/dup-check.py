#!/usr/bin/env python3
"""Muse Brain duplicate check. Stdlib only.

Finds likely-duplicate pages in notes/ and wiki/ before a new note
is filed (Ryven's rule, adapted):
  - SHA-256 exact match  -> duplicate, link to the existing page.
  - Jaccard similarity > 0.72 on word sets -> likely duplicate.

Usage:
  python3 scripts/dup-check.py                 # check all pages
  python3 scripts/dup-check.py notes/new.md    # check one draft
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = [ROOT / "notes", ROOT / "wiki"]
THRESHOLD = 0.72
STOP = set("a an the and or of to in on for with is are was were be by at as it its this that".split())


def words(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[#*`\[\]()\-_>]", " ", text)
    return {w.lower() for w in re.findall(r"[a-z0-9']+", text) if w.lower() not in STOP}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def pages():
    out = []
    for folder in FOLDERS:
        if not folder.exists():
            continue
        for p in sorted(folder.glob("*.md")):
            if p.name == "README.md":
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            out.append((p, text, hashlib.sha256(text.encode()).hexdigest(), words(text)))
    return out


def main():
    all_pages = pages()
    targets = [Path(a) for a in sys.argv[1:]]
    if targets:
        drafts = []
        for t in targets:
            text = Path(t).read_text(encoding="utf-8", errors="ignore")
            drafts.append((Path(t), text, hashlib.sha256(text.encode()).hexdigest(), words(text)))
    else:
        drafts = all_pages
    found = 0
    for dp, dtext, dhash, dwords in drafts:
        for p, _, phash, pwords in all_pages:
            if p.resolve() == dp.resolve():
                continue
            if dhash == phash:
                print(f"DUPLICATE (exact): {dp} == {p}")
                found += 1
            else:
                sim = jaccard(dwords, pwords)
                if sim > THRESHOLD:
                    print(f"LIKELY DUPLICATE (Jaccard {sim:.2f}): {dp} ~ {p}")
                    found += 1
    if not found:
        print("No duplicates found.")
    return 0 if not found else 1


if __name__ == "__main__":
    raise SystemExit(main())
