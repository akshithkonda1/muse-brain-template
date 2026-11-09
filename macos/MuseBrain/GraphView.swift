// GraphView.swift — the premium memory-map graph, drawn with SwiftUI Canvas.
//
// Nodes are the notes, edges are the [[wiki-links]] between them.
// Colour is cluster colour (docs/design-system.md): the same eight
// hues, in the same rank order, as the web dashboard and the Windows
// app. Node size = connections; a ring marks a hub (6+). Cluster
// hulls show each cluster's territory; dashed amber rings are quiet
// notes (no links yet) — invitations, not errors. Drag a node to move
// it, drag the background to pan, pinch/scroll to zoom, click a node
// to read it. Fully local — positions come from BrainStore's seeded,
// cluster-aware force layout, so the same brain draws the same map.

import SwiftUI

/// The shared cluster palette (docs/design-system.md). Same order in
/// the dashboard, the Mac app, and the Windows app.
enum BrainPalette {
    static let cluster: [Color] = [
        Color(red: 0.49, green: 0.36, blue: 1.0),   // violet
        Color(red: 0.08, green: 0.72, blue: 0.65), // teal
        Color(red: 0.96, green: 0.62, blue: 0.04), // amber
        Color(red: 0.96, green: 0.25, blue: 0.37), // rose
        Color(red: 0.05, green: 0.65, blue: 0.91), // sky
        Color(red: 0.06, green: 0.73, blue: 0.51), // emerald
        Color(red: 0.97, green: 0.45, blue: 0.09), // orange
        Color(red: 0.39, green: 0.40, blue: 0.95), // indigo
    ]
    static let warn = Color.orange
    static func clusterColor(_ index: Int) -> Color {
        cluster[index % cluster.count]
    }
}

struct GraphView: View {
    @ObservedObject var store: BrainStore
    @Binding var selectedStem: String?
    @Binding var focusCluster: Int?
    @Binding var showSuggest: Bool
    @State private var scale: CGFloat = 1.0
    @State private var offset: CGSize = .zero
    @State private var panBase: CGSize?
    @State private var dragStem: String?
    @State private var positions: [String: CGPoint] = [:]

    /// Cluster rank of a note (clusters arrive largest-first).
    private func clusterIndex(of stem: String) -> Int? {
        store.clusters.firstIndex { $0.members.contains(stem) }
    }

    private func color(for note: Note) -> Color {
        if let ci = clusterIndex(of: note.stem) {
            return BrainPalette.clusterColor(ci)
        }
        let key = note.tags.first ?? "notes"
        let tags = Set(store.notes.flatMap { $0.tags }).sorted()
        let idx = max(0, tags.firstIndex(of: key) ?? 0)
        return BrainPalette.clusterColor(idx)
    }

    private func degree(of stem: String) -> Int {
        (store.notes.first { $0.stem == stem }?.links.count ?? 0)
            + (store.incoming[stem] ?? []).count
    }

    /// Monotone-chain convex hull, padded outward from the centroid.
    private func hull(of points: [CGPoint], pad: CGFloat) -> [CGPoint] {
        let pts = points.sorted { $0.x < $1.x || ($0.x == $1.x && $0.y < $1.y) }
        guard pts.count >= 3 else { return pts }
        func cross(_ o: CGPoint, _ a: CGPoint, _ b: CGPoint) -> CGFloat {
            (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)
        }
        var lower: [CGPoint] = []
        for p in pts {
            while lower.count >= 2 && cross(lower[lower.count - 2], lower[lower.count - 1], p) <= 0 { lower.removeLast() }
            lower.append(p)
        }
        var upper: [CGPoint] = []
        for p in pts.reversed() {
            while upper.count >= 2 && cross(upper[upper.count - 2], upper[upper.count - 1], p) <= 0 { upper.removeLast() }
            upper.append(p)
        }
        lower.removeLast(); upper.removeLast()
        let h = lower + upper
        let cx = h.reduce(0) { $0 + $1.x } / CGFloat(h.count)
        let cy = h.reduce(0) { $0 + $1.y } / CGFloat(h.count)
        return h.map { p in
            let dx = p.x - cx, dy = p.y - cy, d = max(1, hypot(dx, dy))
            return CGPoint(x: p.x + dx / d * pad, y: p.y + dy / d * pad)
        }
    }

    private func isDim(_ stem: String) -> Bool {
        if let fc = focusCluster {
            return !(store.clusters[safe: fc]?.members.contains(stem) ?? false)
        }
        return false
    }

    var body: some View {
        GeometryReader { geo in
            Canvas { context, size in
                let cx = size.width / 2, cy = size.height / 2
                func pt(_ p: CGPoint) -> CGPoint {
                    CGPoint(x: cx + (p.x - 400) * scale + offset.width,
                            y: cy + (p.y - 260) * scale + offset.height)
                }
                // Cluster hulls, largest first so small hulls draw on top.
                for (ci, cluster) in store.clusters.enumerated()
                    .sorted(by: { $0.element.members.count > $1.element.members.count }) {
                    let pts = cluster.members.compactMap { positions[$0] }
                    guard pts.count >= 3 else { continue }
                    let col = BrainPalette.clusterColor(ci)
                    var path = Path()
                    let h = hull(of: pts, pad: 26)
                    path.move(to: pt(h[0]))
                    for p in h.dropFirst() { path.addLine(to: pt(p)) }
                    path.closeSubpath()
                    context.fill(path, with: .color(col.opacity(0.07)))
                    context.stroke(path, with: .color(col.opacity(0.45)),
                                   style: StrokeStyle(lineWidth: 1.4, dash: [6, 4]))
                    if let top = h.min(by: { $0.y < $1.y }) {
                        context.draw(
                            Text(cluster.label.uppercased())
                                .font(.system(size: 10, weight: .bold))
                                .foregroundStyle(col),
                            at: CGPoint(x: pt(top).x, y: pt(top).y - 10))
                    }
                }
                // Suggested links (dashed accent), when toggled on.
                if showSuggest {
                    for s in store.suggestions {
                        guard let a = positions[s.a], let b = positions[s.b] else { continue }
                        var path = Path()
                        path.move(to: pt(a)); path.addLine(to: pt(b))
                        context.stroke(path, with: .color(.accentColor.opacity(0.65)),
                                       style: StrokeStyle(lineWidth: 1.2, dash: [4, 3]))
                    }
                }
                // Edges
                for note in store.notes {
                    guard let a = positions[note.stem] else { continue }
                    for target in note.links {
                        guard let b = positions[target] else { continue }
                        var path = Path()
                        path.move(to: pt(a))
                        path.addLine(to: pt(b))
                        let dim = isDim(note.stem) || isDim(target)
                        context.stroke(path, with: .color(.secondary.opacity(dim ? 0.08 : 0.35)), lineWidth: 1)
                    }
                }
                // Nodes
                for note in store.notes {
                    guard let p = positions[note.stem] else { continue }
                    let center = pt(p)
                    let deg = degree(of: note.stem)
                    let radius: CGFloat = 8 + min(8, CGFloat(deg))
                    let isOrphan = store.orphans.contains(note.stem)
                    let isSelected = note.stem == selectedStem
                    let col = color(for: note)
                    if deg >= 6 {
                        let ring = Path(ellipseIn: CGRect(
                            x: center.x - radius - 4.5, y: center.y - radius - 4.5,
                            width: (radius + 4.5) * 2, height: (radius + 4.5) * 2))
                        context.stroke(ring, with: .color(col.opacity(0.55)), lineWidth: 1.4)
                    }
                    var circle = Path(ellipseIn: CGRect(
                        x: center.x - radius, y: center.y - radius,
                        width: radius * 2, height: radius * 2))
                    if isOrphan {
                        context.stroke(circle, with: .color(.orange),
                                       style: StrokeStyle(lineWidth: 2, dash: [3, 2]))
                    } else {
                        context.fill(circle, with: .color(col))
                        if isSelected {
                            context.stroke(circle, with: .color(.accentColor), lineWidth: 2)
                        }
                    }
                    if isSelected {
                        var glow = Path(ellipseIn: CGRect(
                            x: center.x - radius - 7, y: center.y - radius - 7,
                            width: (radius + 7) * 2, height: (radius + 7) * 2))
                        context.stroke(glow, with: .color(.accentColor.opacity(0.35)), lineWidth: 5)
                    }
                    // Labels: selected node only — even the hub labels
                    // collide in the centre, because the hubs are all
                    // linked to each other. Names live in the sidebar.
                    if isSelected {
                        let label = note.title.count > 22
                            ? String(note.title.prefix(21)) + "…" : note.title
                        context.draw(Text(label).font(.caption).bold(),
                                     at: CGPoint(x: center.x + radius + 7, y: center.y))
                    }
                }
            }
            .opacity(1)
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { value in
                        if panBase == nil { panBase = offset }
                        if dragStem == nil {
                            let loc = value.location
                            let cx = geo.size.width / 2, cy = geo.size.height / 2
                            var best: (stem: String, dist: CGFloat)? = nil
                            for note in store.notes {
                                guard let p = positions[note.stem] else { continue }
                                let pt = CGPoint(x: cx + (p.x - 400) * scale + offset.width,
                                                 y: cy + (p.y - 260) * scale + offset.height)
                                let d = hypot(loc.x - pt.x, loc.y - pt.y)
                                if d < 16 && (best == nil || d < best!.dist) {
                                    best = (note.stem, d)
                                }
                            }
                            dragStem = best?.stem
                        }
                        if let stem = dragStem {
                            let cx = geo.size.width / 2, cy = geo.size.height / 2
                            positions[stem] = CGPoint(
                                x: 400 + (value.location.x - cx - offset.width) / scale,
                                y: 260 + (value.location.y - cy - offset.height) / scale)
                        } else if let base = panBase {
                            offset = CGSize(width: base.width + value.translation.width,
                                            height: base.height + value.translation.height)
                        }
                    }
                    .onEnded { value in
                        if let stem = dragStem, value.translation == .zero {
                            selectedStem = stem   // it was a tap, not a drag
                        }
                        dragStem = nil
                        panBase = nil
                    }
            )
            .gesture(
                MagnificationGesture()
                    .onChanged { value in scale = max(0.4, min(3, value)) }
            )
        }
        .onAppear { positions = store.positions }
        .onChange(of: store.positions) { _, new in positions = new }
    }
}

extension Array {
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
