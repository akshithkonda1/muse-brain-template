#!/usr/bin/env python3
"""scripts/package.py — build a clean downloadable copy of the brain.

Produces a zip in dist/ that someone can download, unzip, and use
fully offline: the brain (Markdown) + the code (stdlib Python).
No build step, no install, no account, no server.

Excluded from the package, always:
  .git/ and .gitignore'd caches — the download is the brain + code,
  not a cache. Specifically: .git, __pycache__, *.pyc, ml/.cache/,
  *.npz, *.npy, *.pkl, dist/ itself, .DS_Store, and (template only)
  SCRUB-REPORT.md — the staging audit file that names the private
  brain it was scrubbed from. It is gitignored and never packaged.

Usage (run from the repo root):
  python3 scripts/package.py
  # -> dist/<repo>-YYYYMMDD.zip  (name taken from the git remote)

Then test the download the way a stranger would:
  cd /tmp && unzip -q dist/<repo>-*.zip && cd <repo> && python3 scan.py
"""
import datetime
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {".git", "__pycache__", "dist", ".cache"}
EXCLUDE_FILES = {"SCRUB-REPORT.md", ".DS_Store"}
EXCLUDE_SUFFIXES = {".pyc", ".npz", ".npy", ".pkl"}


def repo_name() -> str:
    """Name the zip after the git remote (muse-brain / muse-brain-template)."""
    try:
        url = subprocess.check_output(
            ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
            text=True, stderr=subprocess.DEVNULL).strip()
        name = url.rstrip("/").rsplit("/", 1)[-1]
        if name.endswith(".git"):
            name = name[:-4]
        if name:
            return name
    except Exception:
        pass
    return ROOT.name


def should_include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if path.name in EXCLUDE_FILES:
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


def main() -> int:
    name = repo_name()
    stamp = datetime.date.today().strftime("%Y%m%d")
    out_dir = ROOT / "dist"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{name}-{stamp}.zip"

    files = [p for p in sorted(ROOT.rglob("*"))
             if p.is_file() and should_include(p)]
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, p.relative_to(ROOT))
    size_kb = out_path.stat().st_size // 1024
    print(f"Wrote {out_path} ({len(files)} files, {size_kb} KB).")
    print("Excluded: .git, __pycache__, ml/.cache, *.npz/*.npy/*.pkl, "
          "dist/, SCRUB-REPORT.md.")
    print("To use it: unzip, cd in, then `python3 scan.py` — no install needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
