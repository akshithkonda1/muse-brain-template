// GraphView.swift — the memory-map graph, drawn with SwiftUI Canvas.
//
// Nodes are the notes, edges are the [[wiki-links]] between them.
// Drag a node to move it, drag the background to pan, pinch/scroll to
// zoom, click a node to read it. Node colour = first tag; dashed ring
// = orphan (no links in or out). Fully local — positions come from
// BrainStore's seeded force layout, so the same brain draws the same map.

import SwiftUI

struct GraphView: View {
    @ObservedObject var store: BrainStore
    @Binding var selectedStem: String?
    @State private var scale: CGFloat = 1.0
    @State private var offset: CGSize = .zero
    @State private var panBase: CGSize?
    @State private var dragStem: String?
    @State private var positions: [String: CGPoint] = [:]

    private let tagColors: [Color] = [
        .purple, .teal, .orange, .green, .brown, .blue, .pink, .cyan, .mint, .gray,
    ]

    private func color(for note: Note) -> Color {
        let key = note.tags.first ?? "notes"
        let idx = abs(key.hashValue) % tagColors.count
        return tagColors[idx]
    }

    var body: some View {
        GeometryReader { geo in
            Canvas { context, size in
                let cx = size.width / 2, cy = size.height / 2
                func pt(_ p: CGPoint) -> CGPoint {
                    CGPoint(x: cx + (p.x - 400) * scale + offset.width,
                            y: cy + (p.y - 260) * scale + offset.height)
                }
                // Edges
                for note in store.notes {
                    guard let a = positions[note.stem] else { continue }
                    for target in note.links {
                        guard let b = positions[target] else { continue }
                        var path = Path()
                        path.move(to: pt(a))
                        path.addLine(to: pt(b))
                        context.stroke(path, with: .color(.secondary.opacity(0.5)), lineWidth: 1)
                    }
                }
                // Nodes
                for note in store.notes {
                    guard let p = positions[note.stem] else { continue }
                    let center = pt(p)
                    let radius: CGFloat = 7 + min(6, CGFloat((store.incoming[note.stem] ?? []).count))
                    let isOrphan = store.orphans.contains(note.stem)
                    let isSelected = note.stem == selectedStem
                    var circle = Path(ellipseIn: CGRect(
                        x: center.x - radius, y: center.y - radius,
                        width: radius * 2, height: radius * 2))
                    if isOrphan {
                        context.stroke(circle, with: .color(.orange), style: StrokeStyle(lineWidth: 2, dash: [4, 3]))
                    } else {
                        context.fill(circle, with: .color(color(for: note)))
                    }
                    if isSelected {
                        var ring = Path(ellipseIn: CGRect(
                            x: center.x - radius - 4, y: center.y - radius - 4,
                            width: (radius + 4) * 2, height: (radius + 4) * 2))
                        context.stroke(ring, with: .color(.accentColor), lineWidth: 2.5)
                    }
                    let label = note.title.count > 22
                        ? String(note.title.prefix(21)) + "…" : note.title
                    context.draw(Text(label).font(.caption),
                                 at: CGPoint(x: center.x + radius + 5, y: center.y))
                }
            }
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { value in
                        if panBase == nil { panBase = offset }
                        if dragStem == nil {
                            // Hit-test: nearest node within 16pt?
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
