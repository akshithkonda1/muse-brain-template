#!/bin/sh
# Muse Brain launcher (macOS / Linux) — run the app.
# Requires Python 3.10+. No install, no sudo.
cd "$(dirname "$0")/.." || exit 1
exec python3 app/app.py "$@"
