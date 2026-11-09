# Muse Brain — design system

The single visual language for all three frontends: the web dashboard
(`dashboard.html`), the macOS Swift/SwiftUI app (`macos/`), and the
Windows React Native app (`windows-app/`). The Markdown brain is the
source of truth; this file is the source of truth for how it looks.
If a frontend disagrees with this file, the frontend is wrong.

Everything is offline: no external fonts, scripts, images, or CDN.
Typography is the system font stack on every platform.

## Palette

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--bg` | `#F6F5F1` warm paper | `#0C0B10` | page background |
| `--surface` | `#FFFFFF` | `#16151D` | cards, panels |
| `--surface-2` | `#EFEDE8` | `#1F1E28` | chips, code, hover |
| `--ink` | `#17141F` | `#F4F2FA` | text |
| `--muted` | `#6F6A7E` | `#A19CB6` | secondary text |
| `--line` | `#E3E0D9` | `#2B2938` | borders |
| `--accent` | `#6C4CF1` violet | `#9B7FF5` | primary action, selection |
| `--accent-soft` | `#ECE7FE` | `#2A2340` | accent wash, focus ring |
| `--good` | `#0E7A5F` | `#4ADE9E` | healthy / resolved |
| `--warn` | `#B45309` | `#F5B544` | orphan, stale, attention |
| `--bad` | `#C22744` | `#F26D7D` | broken, duplicate |

The accent is violet — the brain's signature colour. It is the only
saturated colour in chrome; colour on the map itself means *meaning*
(cluster), never decoration.

## Cluster colours

Eight hues, assigned by **cluster rank** — clusters come out of
`ml/search.py` sorted largest-first, and the i-th cluster gets the
i-th colour (wrapping). Every frontend uses the same list, in the
same order, so a cluster is the same colour in the dashboard, the
Mac app, and the Windows app.

```text
0  #7C5CFF  violet     4  #0EA5E9  sky
1  #14B8A6  teal       5  #10B981  emerald
2  #F59E0B  amber      6  #F97316  orange
3  #F43F5E  rose       7  #6366F1  indigo
```

A note's colour is its **cluster colour**, not its first tag — tags
are filters, clusters are the map's geography. A note in no cluster
(singleton) uses its first tag's colour from the same list, keyed by
the tag's position in the sorted tag list.

## Typography

- System stack everywhere: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`.
- Display / note titles: 700 weight, letter-spacing `-0.02em`.
- Eyebrow labels: 11px, uppercase, letter-spacing `0.08em`, muted.
- Body: 15px, line-height 1.55. Captions / meta: 12–13px, muted.
- Numbers in stats use tabular figures; scores use 2 decimals.

## The graph

- **Layout is cluster-aware.** Cluster centres sit on a ring; nodes
  seed around their own cluster's centre, then ~120 force iterations
  (repulsion + link springs + a pull toward the cluster centre) settle
  them. Same brain, same map: the seed is fixed (`7`), so the layout
  is deterministic. Only clusters with 2+ members get their own
  territory — in a small brain most clusters are singletons, and
  giving each one a centre would crowd the ring until every hull
  overlaps. Singletons park on the periphery, grouped by first tag.
  Implemented in `scan.py layout_positions()`, ported in Swift
  (`BrainStore.layoutPositions`) — the Windows app reuses the Python
  positions from `brain-data.json`.
- **Node size = importance.** Radius `8 + min(8, degree)` where degree
  is links in + links out. A note with degree ≥ 6 is a **hub** and gets
  an outer ring.
- **Cluster hulls.** Each cluster with ≥ 2 members gets a soft hull:
  convex hull of its nodes, filled with the cluster colour at 7%
  opacity, stroked dashed at 35%. The hull is the cluster's territory;
  its label sits on the hull's top edge.
- **Edges.** Solid, muted, 35% opacity. A *suggested* link (ML,
  unlinked pair) is drawn dashed in accent violet and can be toggled.
- **Orphans are quiet notes, not broken ones.** Dashed amber ring,
  surface fill, no alarm colour. The legend says "quiet note — no
  links yet", and the attention panel frames them as invitations.
- **Focus.** Clicking a cluster isolates it (others dim to 20%);
  searching highlights hits and dims the rest; clicking a node selects
  it (accent ring + glow) and opens it in the reader. `⌘/Ctrl+K`
  focuses search everywhere. Drag a node to move it; drag the
  background to pan; scroll/pinch to zoom. `Export SVG` downloads
  the graph as a standalone image — the map is made to be shared.

## The markdown map (`MEMORY-MAP.md`)

Generated, never hand-edited (`scripts/memory-map.py`). Premium means
structure, not decoration:

- A title block with the generation date and a one-paragraph "how to
  read this map".
- **At a glance** — a compact stats table, then the top hub notes
  with degree bars (`█` per link).
- **Clusters** — one card per cluster: colour dot, label, size bar,
  members. Largest first.
- **The map, as a diagram** — a Mermaid `flowchart` with one subgraph
  per cluster (top edges only, capped so it stays readable). It
  renders on GitHub, which is the point: the map reads as a picture
  there, not a wall of lists.
- **Quiet notes / attention** — orphans, stale candidates, source
  gaps, tensions, each in its own short section with a one-line
  "what to do" — never a bare dump.
- **Every file** — the full index, grouped by cluster first, then by
  area, with degree bars. Every note stem on disk appears in the map
  (the test suite checks this).

## What never changes

- The map is generated from the real notes. Every node/edge/cluster
  corresponds to a real note, link, or ML cluster. No hand-drawn
  graph, no invented connections.
- `MUSE.md` stays the single map, under 200 lines. Design detail
  lives here, in this file — never in the map.
- Zero external assets. If a frontend needs a font, an icon, or an
  image, it draws it or bundles it.
