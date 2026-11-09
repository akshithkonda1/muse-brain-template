"""Tests for Muse Brain — stdlib-only smoke tests for a fresh download.

These are the "does a stranger's download actually work?" checks.
They run against the repo they live in (private brain or public
template), so they assert shapes, not specific counts: at least one
note, zero broken links, ML that runs stdlib-only, a memory map that
generates and matches the file set.

Run:  pytest            (CI runs this on every push to main)
   or python3 -m pytest
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_scan_finds_notes_with_no_broken_links():
    import scan

    notes = scan.scan_notes()
    assert len(notes) >= 1
    _, broken, _orphans = scan.build_graph(notes)
    assert broken == []


def test_ml_search_runs_stdlib_only():
    from ml.search import Index, load_corpus

    docs = load_corpus()
    assert len(docs) >= 1
    idx = Index(docs)
    # A query made of words that exist in the corpus must rank something.
    common = docs[0]["tokens"][0] if docs[0]["tokens"] else "brain"
    results = idx.search(common)
    assert len(results) >= 1
    assert idx.clusters()  # at least one cluster, even for 3 notes


def test_dup_check_clean():
    proc = subprocess.run(
        [sys.executable, "scripts/dup-check.py"],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout


def test_memory_map_generates_and_matches(tmp_path):
    work = tmp_path / "brain-copy"
    shutil.copytree(ROOT, work,
                    ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                  ".cache", "dist"))
    proc = subprocess.run(
        [sys.executable, "scripts/memory-map.py"],
        cwd=work, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    mmap = work / "MEMORY-MAP.md"
    assert mmap.exists()
    text = mmap.read_text(encoding="utf-8")
    assert "0 broken" in text
    # Every note file on disk appears in the map.
    for note in (work / "notes").glob("*.md"):
        assert note.stem in text


def test_package_builds_clean_zip(tmp_path):
    proc = subprocess.run(
        [sys.executable, "scripts/package.py"],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    zips = list((ROOT / "dist").glob("*.zip"))
    assert zips, "package.py wrote no zip"
    import zipfile

    names = zipfile.ZipFile(zips[0]).namelist()
    assert "MUSE.md" in names and "scan.py" in names
    assert not any(n.startswith(".git/") or n == "SCRUB-REPORT.md"
                   or ".cache" in n or n.endswith((".npz", ".pkl"))
                   for n in names)


def test_dashboard_is_offline_polished_app():
    """dashboard.html is the real UI: embedded data, no external assets."""
    import json as _json

    proc = subprocess.run(
        [sys.executable, "scan.py"],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    html = (ROOT / "dashboard.html").read_text(encoding="utf-8")
    assert "/*__BRAIN_JSON__*/" not in html  # placeholder replaced by data
    assert "const BRAIN =" in html
    assert 'src="http' not in html and "href=\"http" not in html
    for marker in ('id="graph"', 'id="q"', 'id="reader"',
                   'id="tagChips"', 'id="clusterList"', 'data-theme'):
        assert marker in html, marker
    start = html.index("const BRAIN = ") + len("const BRAIN = ")
    data, _ = _json.JSONDecoder().raw_decode(html[start:])
    assert len(data["notes"]) >= 1
    assert len(data["positions"]) == len(data["notes"])
    assert data["clusters"] is not None and data["idf"]


def test_app_api_serves_search_and_notes():
    """The stdlib app server answers /api/search, /api/notes, 404s."""
    import socket
    import time
    import urllib.request

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen(
        [sys.executable, "app/app.py", "--port", str(port), "--no-browser"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True)
    try:
        base = f"http://127.0.0.1:{port}"
        deadline = time.time() + 10
        while True:
            try:
                with urllib.request.urlopen(base + "/", timeout=2) as r:
                    assert r.status == 200
                    break
            except Exception:
                if time.time() > deadline:
                    raise AssertionError("app server did not start:\n"
                                         + (proc.stdout.read() or ""))
                time.sleep(0.3)
        import json as _json
        with urllib.request.urlopen(base + "/api/search?q=brain") as r:
            body = _json.load(r)
        assert body["results"], "search returned nothing"
        stem = body["results"][0]["stem"]
        with urllib.request.urlopen(base + f"/api/notes/{stem}") as r:
            note = _json.load(r)
        assert note["stem"] == stem and len(note["text"]) > 0
        try:
            urllib.request.urlopen(base + "/api/notes/no-such-note")
            raise AssertionError("expected 404 for unknown note")
        except urllib.error.HTTPError as e:
            assert e.code == 404
    finally:
        proc.terminate()
        proc.wait(timeout=5)
