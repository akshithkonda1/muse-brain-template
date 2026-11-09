// ContentView.swift — the main window: sidebar + graph + reader.
//
// Three panes, all local: search (BM25, same math as ml/search.py),
// the memory-map graph, and the note reader. Dark/light follows the
// system, with a manual override in the toolbar. Nothing here talks
// to the network.

import SwiftUI

struct ContentView: View {
    @ObservedObject var store: BrainStore
    @State private var query = ""
    @State private var selectedStem: String?
    @State private var activeTags: Set<String> = []
    @State private var focusCluster: Int? = nil
    @State private var showSuggest = false
    @State private var theme: String = "system"
    @FocusState private var searchFocused: Bool

    private var searchHits: [(note: Note, score: Double, bm25: Double, cosine: Double)] {
        query.trimmingCharacters(in: .whitespaces).isEmpty
            ? [] : store.search(query)
    }

    private var visibleNotes: [Note] {
        if !searchHits.isEmpty { return searchHits.map { $0.note } }
        if !activeTags.isEmpty {
            return store.notes.filter { !Set($0.tags).isDisjoint(with: activeTags) }
        }
        return store.notes
    }

    private var selectedNote: Note? {
        selectedStem.flatMap { stem in store.notes.first { $0.stem == stem } }
    }

    /// Most-connected notes first — the fastest way back into the brain.
    private var hubs: [(note: Note, degree: Int)] {
        store.notes.map { note in
            (note, note.links.count + (store.incoming[note.stem] ?? []).count)
        }.sorted { $0.degree > $1.degree }.prefix(6).map { $0 }
    }

    var body: some View {
        NavigationSplitView {
            sidebar
        } detail: {
            HSplitView {
                graphPane
                readerPane
            }
        }
        .preferredColorScheme(theme == "system" ? nil
            : (theme == "dark" ? .dark : .light))
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Menu {
                    Button("System") { theme = "system" }
                    Button("Light") { theme = "light" }
                    Button("Dark") { theme = "dark" }
                } label: {
                    Label("Theme", systemImage: "circle.lefthalf.filled")
                }
            }
            ToolbarItem(placement: .primaryAction) {
                Button("Refresh") { store.refresh() }
                    .keyboardShortcut("r", modifiers: .command)
                    .help("Re-read the brain folder from disk")
            }
            ToolbarItem(placement: .primaryAction) {
                Button("Choose folder…") { store.chooseFolder() }
            }
        }
        .onAppear { searchFocused = true }
    }

    // MARK: - Sidebar

    private var sidebar: some View {
        List {
            Section {
                TextField("Search the brain…  (⌘K)", text: $query)
                    .textFieldStyle(.roundedBorder)
                    .focused($searchFocused)
                    .onSubmit { if let first = searchHits.first { selectedStem = first.note.stem } }
                if !searchHits.isEmpty {
                    ForEach(searchHits, id: \.note.stem) { hit in
                        Button {
                            selectedStem = hit.note.stem
                        } label: {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(hit.note.title).font(.headline)
                                Text(String(format: "BM25 %.2f", hit.score))
                                    .font(.caption).foregroundStyle(.secondary)
                            }
                        }
                        .buttonStyle(.plain)
                    }
                }
            } header: {
                Text("Search — BM25, offline")
            }

            Section("Brain") {
                LabeledContent("Notes", value: "\(store.notes.count)")
                LabeledContent("Links", value: "\(store.notes.map { $0.links.count }.reduce(0, +))")
                LabeledContent("Clusters", value: "\(store.clusters.count)")
                LabeledContent("Orphans", value: "\(store.orphans.count)")
            }

            Section("Tags") {
                FlowLayout(spacing: 6) {
                    ForEach(store.tagCounts.sorted(by: { $0.value > $1.value }), id: \.key) { tag, count in
                        Button("#\(tag) · \(count)") {
                            if activeTags.contains(tag) { activeTags.remove(tag) }
                            else { activeTags.insert(tag) }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .tint(activeTags.contains(tag) ? .accentColor : nil)
                    }
                }
            }

            Section("Hubs — start here") {
                ForEach(hubs, id: \.note.stem) { hub in
                    Button {
                        selectedStem = hub.note.stem
                    } label: {
                        HStack {
                            Text(hub.note.title).font(.headline)
                            Spacer()
                            Text("\(hub.degree) links")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .buttonStyle(.plain)
                }
            }

            Section("Clusters") {
                ForEach(Array(store.clusters.enumerated()), id: \.element.id) { ci, cluster in
                    HStack(alignment: .top, spacing: 8) {
                        Circle()
                            .fill(BrainPalette.clusterColor(ci))
                            .frame(width: 10, height: 10)
                            .padding(.top, 4)
                        VStack(alignment: .leading, spacing: 2) {
                            Text(cluster.label).font(.headline)
                            Text(cluster.members.joined(separator: ", "))
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .contentShape(Rectangle())
                    .onTapGesture {
                        activeTags = []
                        focusCluster = (focusCluster == ci) ? nil : ci
                        if let first = cluster.members.first { selectedStem = first }
                    }
                    .opacity(focusCluster == nil || focusCluster == ci ? 1 : 0.45)
                }
            }

            Section("Needs attention") {
                if !store.orphans.isEmpty {
                    DisclosureGroup("Orphans (\(store.orphans.count))") {
                        ForEach(store.orphans, id: \.self) { stem in
                            Button(stem) { selectedStem = stem }.buttonStyle(.plain)
                        }
                    }
                }
                if !store.stale.isEmpty {
                    DisclosureGroup("Stale — 90+ days (\(store.stale.count))") {
                        ForEach(store.stale, id: \.self) { stem in
                            Button(stem) { selectedStem = stem }.buttonStyle(.plain)
                        }
                    }
                }
                if !store.suggestions.isEmpty {
                    DisclosureGroup("Link suggestions (\(store.suggestions.count))") {
                        ForEach(store.suggestions.prefix(8)) { s in
                            Text("\(s.a) ↔ \(s.b)").font(.caption)
                        }
                    }
                }
                if store.duplicates.isEmpty && store.orphans.isEmpty && store.stale.isEmpty {
                    Text("Nothing needs attention.").foregroundStyle(.secondary)
                }
            }
        }
        .listStyle(.sidebar)
        .navigationTitle("Muse Brain")
    }

    // MARK: - Graph + reader

    private var graphPane: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Memory map").font(.headline)
                Spacer()
                Text("\(visibleNotes.count) notes · \(store.clusters.count) clusters")
                    .font(.caption).foregroundStyle(.secondary)
                Button(showSuggest ? "Hide suggestions" : "Suggestions") {
                    showSuggest.toggle()
                }
                .buttonStyle(.bordered)
                .controlSize(.small)
            }
            .padding(.horizontal)
            GraphView(store: store, selectedStem: $selectedStem,
                      focusCluster: $focusCluster, showSuggest: $showSuggest)
                .frame(minWidth: 320, minHeight: 320)
            HStack(spacing: 12) {
                ForEach(Array(store.clusters.prefix(8).enumerated()), id: \.offset) { ci, cluster in
                    HStack(spacing: 4) {
                        Circle().fill(BrainPalette.clusterColor(ci)).frame(width: 9, height: 9)
                        Text(cluster.label.split(separator: ",").first.map(String.init) ?? cluster.label)
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
                Text("ring = hub (6+) · dashed = quiet note")
                    .font(.caption).foregroundStyle(.secondary)
            }
            .padding(.horizontal)
            Text("Drag a node to move it · drag the background to pan · pinch to zoom · click a node to read it · click a cluster to focus it.")
                .font(.caption).foregroundStyle(.secondary)
                .padding(.horizontal)
        }
        .padding(.vertical, 8)
    }

    private var readerPane: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 8) {
                if let note = selectedNote {
                    Text(note.title).font(.largeTitle).bold()
                    Text("\(note.fileURL.lastPathComponent) · \(note.tags.map { "#\($0)" }.joined(separator: " ")) · \(note.links.count) links out · \((store.incoming[note.stem] ?? []).count) in")
                        .font(.caption).foregroundStyle(.secondary)
                    MarkdownText(markdown: note.text) { stem in
                        selectedStem = stem
                    }
                    if !store.related(to: note.stem).isEmpty {
                        Divider()
                        Text("Related").font(.headline)
                        ForEach(store.related(to: note.stem), id: \.note.stem) { rel in
                            Button("\(rel.note.title)  (\(String(format: "%.2f", rel.cosine)))") {
                                selectedStem = rel.note.stem
                            }
                            .buttonStyle(.plain)
                        }
                    }
                } else {
                    Text("Welcome to Muse Brain").font(.largeTitle).bold()
                    Text("Pick a note from the graph, the search box, or a list. Everything here is local — the notes, the search index, and the graph all come from the Markdown files in your brain folder. No network, no account, no server.")
                        .foregroundStyle(.secondary)
                    Text("Start with search (ranked by BM25, the same index the Python ml/search.py tool uses), or explore a cluster on the left.")
                }
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .frame(minWidth: 300)
    }
}

/// A real wrapping flow layout for the tag chips.
struct FlowLayout: Layout {
    var spacing: CGFloat = 6

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews,
                      cache: inout ()) -> CGSize {
        let sizes = subviews.map { $0.sizeThatFits(.unspecified) }
        let maxWidth = proposal.width ?? .infinity
        var width: CGFloat = 0, height: CGFloat = 0
        var rowWidth: CGFloat = 0, rowHeight: CGFloat = 0
        for size in sizes {
            if rowWidth > 0 && rowWidth + size.width > maxWidth {
                width = max(width, rowWidth)
                height += rowHeight + spacing
                rowWidth = 0; rowHeight = 0
            }
            rowWidth += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        width = max(width, rowWidth)
        height += rowHeight
        return CGSize(width: width, height: height)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize,
                       subviews: Subviews, cache: inout ()) {
        let sizes = subviews.map { $0.sizeThatFits(.unspecified) }
        var x = bounds.minX, y = bounds.minY, rowHeight: CGFloat = 0
        for (index, subview) in subviews.enumerated() {
            let size = sizes[index]
            if x > bounds.minX && x + size.width > bounds.maxX {
                x = bounds.minX
                y += rowHeight + spacing
                rowHeight = 0
            }
            subview.place(at: CGPoint(x: x, y: y), proposal: .unspecified)
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
    }
}
