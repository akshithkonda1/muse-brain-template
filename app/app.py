#!/usr/bin/env python3
"""app/app.py — the Muse Brain local app server. Stdlib only.

Serves the brain folder over HTTP on localhost and adds a small
JSON API backed by the same ML code the brain already ships:

  GET /                     -> dashboard.html (the polished UI)
  GET /api/search?q=...     -> ranked ML search (BM25 + TF-IDF cosine)
  GET /api/related?stem=..  -> notes most related to one note
  GET /api/map              -> stats, clusters, orphans, stale flags
  GET /api/notes/<stem>     -> one note's Markdown text
  Any other path            -> the file itself, from the repo root

Everything runs on this machine. No account, no cloud, no telemetry,
no database. The Markdown files stay the source of truth — the app
is a viewer/runner over them, not a replacement.

Usage:
  python3 app/app.py                # http://127.0.0.1:8321, opens browser
  python3 app/app.py --port 8080 --no-browser
  python3 app/app.py --root ~/other-brain   # serve a different folder

The native apps are separate frontends over the same brain (see
docs/installers.md): Swift/SwiftUI for the macOS .dmg, React Native
Windows for the Windows .exe. This server is the no-install way to
run the same dashboard + live ML API on any machine.
"""
import argparse
import json
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_PORT = 8321


def _json(handler, obj, status=200):
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class BrainHandler(SimpleHTTPRequestHandler):
    """Static files from the repo root, plus /api/* from ml/search.py."""

    def log_message(self, *args):  # keep the console quiet
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._handle_api(parsed)
            return
        if parsed.path in ("/", ""):
            self.path = "/dashboard.html"
        super().do_GET()

    def _handle_api(self, parsed):
        qs = parse_qs(parsed.query)
        try:
            from ml.search import Index, load_corpus
        except Exception as exc:  # ML must never break the server
            _json(self, {"error": f"ML unavailable: {exc}"}, status=500)
            return
        docs = load_corpus()
        idx = Index(docs)
        if parsed.path == "/api/search":
            q = qs.get("q", [""])[0]
            top = int(qs.get("top", ["5"])[0])
            results = [{
                "stem": r["doc"]["stem"],
                "title": r["doc"]["title"],
                "bm25": r["bm25"],
                "cosine": r["cosine"],
                "score": r["score"],
            } for r in idx.search(q, top)]
            _json(self, {"query": q, "results": results})
        elif parsed.path == "/api/related":
            stem = qs.get("stem", [""])[0]
            top = int(qs.get("top", ["5"])[0])
            results = [{
                "stem": r["doc"]["stem"],
                "title": r["doc"]["title"],
                "cosine": r["cosine"],
            } for r in idx.related(stem, top)]
            _json(self, {"stem": stem, "results": results})
        elif parsed.path == "/api/map":
            _json(self, {
                "docs": len(docs),
                "clusters": idx.clusters(),
                "suggest_links": [{
                    "a": s["a"]["stem"], "b": s["b"]["stem"],
                    "cosine": s["cosine"],
                } for s in idx.suggest_links()],
                "duplicates": idx.duplicates(),
            })
        elif parsed.path.startswith("/api/notes/"):
            stem = parsed.path.rsplit("/", 1)[-1]
            doc = next((d for d in docs if d["stem"] == stem), None)
            if doc is None:
                _json(self, {"error": f"no such note: {stem}"}, status=404)
            else:
                _json(self, {"stem": doc["stem"], "title": doc["title"],
                             "tags": doc["tags"], "text": doc["text"]})
        else:
            _json(self, {"error": "unknown api path"}, status=404)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="muse-brain-app")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--root", type=Path, default=ROOT,
                   help="brain folder to serve (default: this repo)")
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args(argv)

    root = args.root.resolve()
    if not (root / "dashboard.html").exists():
        print(f"No dashboard.html under {root} — run `python3 scan.py` "
              "there first.", file=sys.stderr)
        return 1
    handler = partial(BrainHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    print(f"Muse Brain running at {url}  (serving {root})")
    print("Press Ctrl+C to stop. Notes stay as Markdown files — the app "
          "only reads them.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
