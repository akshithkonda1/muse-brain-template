# Muse Brain — macOS app (Swift / SwiftUI)

The native macOS frontend for the Muse Brain. It reads the Markdown
brain folder straight off disk — no server, no cloud, no account.

## What it does

- **Sidebar:** BM25 search (same math as `ml/search.py`), brain stats,
  tag chips, topic clusters, and a "needs attention" list
  (orphans, stale 90+ days, link suggestions, duplicates).
- **Memory-map graph:** nodes = notes, edges = `[[wiki-links]]`,
  drag a node to move it, drag the background to pan, pinch to zoom,
  click a node to read it. Dashed ring = orphan.
- **Reader:** renders the note's Markdown, `[[links]]` navigate
  inside the app, related notes underneath (TF-IDF cosine).
- **Theme:** system / light / dark from the toolbar.
- **Brain folder:** saved choice, a `Brain/` folder next to the
  `.app`, `~/MuseBrain`, or `~/Documents/MuseBrain` — otherwise it
  asks you to choose one. Refresh (Cmd+R) re-reads the folder.

## Build it on a Mac

Requirements: macOS 14+, Xcode 15+ (free from the App Store).

```bash
git clone https://github.com/akshithkonda1/muse-brain-template.git
cd muse-brain
open macos/MuseBrain.xcodeproj
# Product → Run (⌘R). Or from the terminal:
xcodebuild -project macos/MuseBrain.xcodeproj \
  -scheme MuseBrain -configuration Release build
```

The built app lands in `~/Library/Developer/Xcode/DerivedData/…/Build/Products/Release/MuseBrain.app`.
Copy it next to a `Brain/` folder (the repo root works) or point it
at a folder on first launch.

## Make a .dmg

```bash
# After the Release build above, stage + image it:
APP=$(find ~/Library/Developer/Xcode/DerivedData -name MuseBrain.app -path "*Release*" | head -1)
rm -rf /tmp/MuseBrain-dmg && mkdir -p /tmp/MuseBrain-dmg
cp -R "$APP" /tmp/MuseBrain-dmg/
cp -R . /tmp/MuseBrain-dmg/Brain   # the brain the .dmg ships with
ln -s /Applications /tmp/MuseBrain-dmg/Applications
hdiutil create -volname MuseBrain -srcfolder /tmp/MuseBrain-dmg \
  -ov -format UDZO MuseBrain.dmg
```

The GitHub Actions workflow (`.github/workflows/build.yml`, job
`build-macos`) does exactly this on `macos-latest` and uploads the
`.dmg` as an artifact. First run it from the repo's **Actions** tab
(workflow_dispatch).

## Signing

The build is **unsigned** unless you sign it: set your Development
Team in Xcode (Signing & Capabilities) or pass
`CODE_SIGN_IDENTITY="Developer ID Application: …"` to xcodebuild.
Unsigned: macOS Gatekeeper blocks the first open — right-click the
app → **Open** → **Open**. For a .dmg people download, notarization
needs an Apple Developer ID ($99/yr) — not required for personal use.

## Files

| File | What it is |
|---|---|
| `MuseBrainApp.swift` | `@main`, window, welcome screen |
| `Models.swift` | Note / Cluster / LinkSuggestion / DuplicateFlag |
| `BrainStore.swift` | Loads + parses the brain folder, graph layout |
| `SearchEngine.swift` | BM25 + TF-IDF cosine, clusters, duplicates (port of `ml/search.py`) |
| `MarkdownText.swift` | Markdown → AttributedString, `[[x]]` → in-app links |
| `GraphView.swift` | SwiftUI Canvas graph (pan / zoom / drag / tap) |
| `ContentView.swift` | Sidebar + graph + reader |
| `Info.plist` | App bundle metadata |

Bundle ID is `com.musebrain.app` — change it to your own reverse
domain before signing for distribution.
