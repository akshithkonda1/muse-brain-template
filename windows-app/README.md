# Muse Brain — Windows app (React Native Windows)

The native Windows frontend for the Muse Brain: a React Native
Windows app that produces a real `.exe`. No Electron, no web view —
native Windows UI, reading the local Markdown brain, fully offline.

## What it does

- **Sidebar:** BM25 search (same math as `ml/search.py` and the Swift
  app), brain stats, tag chips, topic clusters, and a "needs
  attention" list (orphans, stale 90+ days, link suggestions,
  duplicates).
- **Memory-map graph:** nodes = notes, edges = `[[wiki-links]]`,
  drag the background to pan, tap a node to read it, zoom buttons.
  Dashed ring = orphan.
- **Reader:** renders the note's Markdown, `[[links]]` navigate
  inside the app, related notes underneath (TF-IDF cosine).
- **Theme:** light / dark toggle in the header.
- **Offline:** no network, no account, no server, no API keys.

## How the data gets in

React Native Windows has no stable built-in way to read arbitrary
files off disk from JS, so v1 ships the brain as a **bundled
snapshot**: `src/brain-data.json`, generated from the Markdown files
(the source of truth) by `scripts/generate-brain-data.py`, which
reuses the repo's own `scan.py` + `ml/search.py`. Re-run it after
editing notes, before building:

```powershell
npm run brain-data        # from windows-app/
```

A "choose brain folder" that reads `.md` files live from disk is a
follow-up — it needs a small WinRT `StorageFile` native bridge, not
a bundled file. It is not faked here.

Note: the app's orphan count covers notes/ + wiki/ (in this template:
the wiki page `second-brain-pattern`), while `dashboard.html` counts
notes/ only (0). Same notes, different scope.

## Build it on Windows

Requirements: Windows 10/11, Node 20 LTS, Visual Studio 2022 with
the **Desktop development with C++** workload (GitHub's
`windows-latest` runners already have it).

```powershell
git clone https://github.com/akshithkonda1/muse-brain-template.git
cd muse-brain\windows-app
npm ci
npm run brain-data
npx react-native-windows-init --overwrite --version 0.76.5
npx react-native run-windows --release --arch x64 --no-packager --no-launch
```

The built app lands in
`windows-app\windows\x64\Release\MuseBrain\MuseBrain.exe`
(next to its DLLs — ship the whole `MuseBrain` folder, not the
`.exe` alone). The first `react-native-windows-init` run generates
the `windows\` native project (C++ / MSBuild); it is not committed
— the workflow regenerates it every build.

## The .exe from GitHub Actions

`.github/workflows/build.yml`, job `build-windows`, runs on
`windows-latest`: installs Node 20, `npm ci`, regenerates
`brain-data.json`, runs the init + release build, and uploads the
`MuseBrain` Release folder (`.exe` + DLLs) as an artifact. Run it
from the repo's **Actions** tab (workflow_dispatch) and download the
artifact. There is no installer wrapper yet — unzip and run
`MuseBrain.exe`.

## Signing

The build is **unsigned** unless you sign it: an EV code-signing
certificate (or Azure Trusted Signing) is needed to avoid
SmartScreen warnings on other people's machines. Not required for
personal use — Windows will warn once ("Run anyway").

## Files

| File | What it is |
|---|---|
| `package.json` / `package-lock.json` | react-native 0.76.5 + react-native-windows 0.76.5 + react-native-svg |
| `app.json` | App name `MuseBrain` |
| `metro.config.js` | Metro bundler config (`.md` as assets) |
| `babel.config.js` | Babel preset |
| `index.js` | AppRegistry entry point |
| `src/App.tsx` | Window: sidebar + graph + reader |
| `src/brain.ts` | Types + bundled brain data |
| `src/search.ts` | BM25 + TF-IDF cosine (port of `ml/search.py`) |
| `src/markdown.tsx` | Tiny Markdown → RN Text renderer |
| `src/GraphView.tsx` | react-native-svg graph (pan / tap / zoom) |
| `src/brain-data.json` | Generated snapshot — regenerate, don't hand-edit |
| `scripts/generate-brain-data.py` | Builds the snapshot from the Markdown brain |
