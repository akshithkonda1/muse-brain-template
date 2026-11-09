// BrainStore.swift — loads the Markdown brain from a local folder.
//
// The brain folder is the source of truth: notes/, wiki/, memory.md,
// and friends, read straight off disk. No server, no cloud, no
// database. The store re-reads the folder on demand (Refresh button
// / Cmd+R); the app never writes into it except when you explicitly
// ask it to save a note edit — and even then only as Markdown.

import Foundation
import AppKit
import Combine

@MainActor
final class BrainStore: ObservableObject {
    @Published var brainFolder: URL?
    @Published var notes: [Note] = []
    @Published var incoming: [String: [String]] = [:]
    @Published var brokenLinks: [(source: String, target: String)] = []
    @Published var orphans: [String] = []
    @Published var stale: [String] = []          // unchanged 90+ days
    @Published var sourceGaps: [String] = []     // "[source needed]" / no source
    @Published var clusters: [Cluster] = []
    @Published var suggestions: [LinkSuggestion] = []
    @Published var duplicates: [DuplicateFlag] = []
    @Published var positions: [String: CGPoint] = [:]
    @Published var loadError: String?

    private let folderKey = "muse-brain-folder"
    private var index: SearchEngine.Index?

    var tagCounts: [String: Int] {
        var counts: [String: Int] = [:]
        for note in notes { for tag in note.tags { counts[tag, default: 0] += 1 } }
        return counts
    }

    init() {
        if let folder = Self.defaultFolder() {
            load(from: folder)
        }
    }

    // MARK: - Finding the brain

    /// Where the brain lives, in order: saved choice, a "Brain" folder
    /// next to the .app, ~/MuseBrain, ~/Documents/MuseBrain.
    static func defaultFolder() -> URL? {
        if let saved = UserDefaults.standard.string(forKey: "muse-brain-folder"),
           !saved.isEmpty {
            let url = URL(fileURLWithPath: saved)
            if FileManager.default.fileExists(atPath: url.path) { return url }
        }
        let fm = FileManager.default
        if let appDir = Bundle.main.bundleURL.deletingLastPathComponent() as URL? {
            let nextToApp = appDir.appendingPathComponent("Brain")
            if fm.fileExists(atPath: nextToApp.path) { return nextToApp }
        }
        let home = fm.homeDirectoryForCurrentUser
        for candidate in [home.appendingPathComponent("MuseBrain"),
                          home.appendingPathComponent("Documents/MuseBrain")] {
            if fm.fileExists(atPath: candidate.path) { return candidate }
        }
        return nil
    }

    func chooseFolder() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = false
        panel.message = "Choose the folder holding your Muse Brain (the one with notes/ and MUSE.md)."
        panel.prompt = "Choose brain folder"
        if panel.runModal() == .OK, let url = panel.url {
            UserDefaults.standard.set(url.path, forKey: folderKey)
            load(from: url)
        }
    }

    // MARK: - Loading

    func load(from folder: URL) {
        brainFolder = folder
        let fm = FileManager.default
        var loaded: [Note] = []
        for area in ["notes", "wiki"] {
            let dir = folder.appendingPathComponent(area)
            guard let files = try? fm.contentsOfDirectory(
                at: dir, includingPropertiesForKeys: [.contentModificationDateKey]) else { continue }
            for file in files where file.pathExtension == "md" && file.lastPathComponent != "README.md" {
                guard let text = try? String(contentsOf: file, encoding: .utf8) else { continue }
                let mtime = (try? file.resourceValues(forKeys: [.contentModificationDateKey]))?.contentModificationDate ?? Date()
                loaded.append(Note(
                    stem: file.deletingPathExtension().lastPathComponent,
                    title: Self.firstHeading(in: text) ?? file.deletingPathExtension().lastPathComponent,
                    tags: Self.tags(in: text),
                    links: Self.links(in: text),
                    text: text,
                    fileURL: file,
                    area: area,
                    modified: mtime))
            }
        }
        loaded.sort { $0.stem < $1.stem }
        notes = loaded

        let stems = Set(notes.map { $0.stem })
        var incoming: [String: [String]] = [:]
        var broken: [(String, String)] = []
        for note in notes {
            for target in note.links {
                if stems.contains(target) { incoming[target, default: []].append(note.stem) }
                else { broken.append((note.stem, target)) }
            }
        }
        self.incoming = incoming
        self.brokenLinks = broken
        orphans = notes.filter { $0.links.isEmpty && (incoming[$0.stem] ?? []).isEmpty }.map { $0.stem }
        let ninetyDaysAgo = Date().addingTimeInterval(-90 * 86400)
        stale = notes.filter { $0.modified < ninetyDaysAgo }.map { $0.stem }
        sourceGaps = notes.filter {
            $0.text.contains("[source needed]") ||
            (!Self.hasSourceLine($0.text) && $0.area == "notes")
        }.map { $0.stem }

        let idx = SearchEngine.Index(notes: notes)
        index = idx
        clusters = idx.clusters()
        suggestions = idx.suggestLinks()
        duplicates = idx.duplicates()
        positions = Self.layoutPositions(notes: notes, clusters: clusters)
        loadError = nil
    }

    func refresh() {
        if let folder = brainFolder { load(from: folder) }
    }

    // MARK: - Search (delegates to the index)

    func search(_ query: String, top: Int = 8) -> [(note: Note, score: Double, bm25: Double, cosine: Double)] {
        index?.search(query, top: top) ?? []
    }

    func related(to stem: String, top: Int = 5) -> [(note: Note, cosine: Double)] {
        index?.related(to: stem, top: top) ?? []
    }

    // MARK: - Parsing

    private static func firstHeading(in text: String) -> String? {
        for line in text.components(separatedBy: .newlines) {
            if line.hasPrefix("# ") { return String(line.dropFirst(2)).trimmingCharacters(in: .whitespaces) }
        }
        return nil
    }

    private static func tags(in text: String) -> [String] {
        let pattern = "#([A-Za-z][A-Za-z0-9_-]*)"
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return [] }
        let range = NSRange(text.startIndex..., in: text)
        return Set(regex.matches(in: text, range: range).compactMap {
            Range($0.range(at: 1), in: text).map { String(text[$0]) }
        }).sorted()
    }

    private static func links(in text: String) -> [String] {
        // Links inside `inline code` are mentions, not real links.
        let stripped = text.replacingOccurrences(
            of: "`[^`]*`", with: " ", options: .regularExpression)
        let pattern = "\\[\\[([^\\]|#]+)(?:#[^\\]]*)?(?:\\|[^\\]]*)?\\]\\]"
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return [] }
        let range = NSRange(stripped.startIndex..., in: stripped)
        return Set(regex.matches(in: stripped, range: range).compactMap {
            Range($0.range(at: 1), in: stripped).map {
                String(stripped[$0]).trimmingCharacters(in: .whitespaces)
                    .lowercased().replacingOccurrences(of: " ", with: "-")
            }
        }).sorted()
    }

    private static func hasSourceLine(_ text: String) -> Bool {
        text.components(separatedBy: .newlines).contains {
            $0.trimmingCharacters(in: .whitespaces).hasPrefix("Source:")
                || $0.contains("(per ")
        }
    }

    // MARK: - Graph layout (seeded, cluster-aware force layout, port of scan.py)
    //
    // Cluster centres sit on a ring; nodes seed around their own
    // cluster's centre, then force iterations (repulsion + link
    // springs + a pull toward the cluster centre) settle them.
    // Same brain, same map. Colours follow docs/design-system.md:
    // cluster rank = colour rank.

    /// Deterministic positions in an 800x520 space. Same brain, same map.
    static func layoutPositions(notes: [Note], clusters: [Cluster] = []) -> [String: CGPoint] {
        guard !notes.isEmpty else { return [:] }
        var rng = SeededRandom(seed: 7)
        let stems = notes.map { $0.stem }
        // Only clusters with 2+ members get their own territory —
        // singletons are parked on the periphery, grouped by first tag.
        var clusterOf: [String: Int] = [:]
        let major = clusters.filter { $0.members.count >= 2 }
        for (ci, c) in clusters.enumerated() where major.contains(c) {
            for m in c.members { clusterOf[m] = ci }
        }
        if clusters.isEmpty {
            let groups = Dictionary(grouping: notes) { $0.tags.first ?? "notes" }
            let names = Array(groups.keys)
            for (gi, key) in names.enumerated() {
                for note in groups[key] ?? [] { clusterOf[note.stem] = gi }
            }
        }
        var peripheral: [String: [String]] = [:]
        for note in notes where clusterOf[note.stem] == nil {
            peripheral[note.tags.first ?? "notes", default: []].append(note.stem)
        }
        let groupOrder = Array(Set(clusterOf.values)).sorted()
        for (gi, key) in peripheral.keys.sorted().enumerated() {
            for stem in peripheral[key] ?? [] { clusterOf[stem] = 1000 + gi }
        }
        let nGroups = groupOrder.count + peripheral.count
        func clusterCenter(_ ci: Int) -> CGPoint {
            if ci >= 1000 {
                let gi = ci - 1000
                let base = Double(groupOrder.count + gi) / Double(max(nGroups, 1)) * 2 * Double.pi
                return CGPoint(x: 400 + 205 * cos(base), y: 260 + 165 * sin(base))
            }
            let idx = groupOrder.firstIndex(of: ci) ?? 0
            let base = Double(idx) / Double(max(nGroups, 1)) * 2 * Double.pi
            return CGPoint(x: 400 + 165 * cos(base), y: 260 + 135 * sin(base))
        }
        var pos: [String: CGPoint] = [:]
        for note in notes {
            let cc = clusterCenter(clusterOf[note.stem] ?? 0)
            let a = rng.next() * 2 * Double.pi
            let r = 28 + rng.next() * 52
            pos[note.stem] = CGPoint(x: cc.x + r * cos(a), y: cc.y + r * 0.8 * sin(a))
        }
        var edges: [(String, String)] = []
        for note in notes {
            for t in note.links where stems.contains(t) && t != note.stem {
                edges.append((note.stem, t))
            }
        }
        for _ in 0..<120 {
            var forces: [String: CGPoint] = Dictionary(uniqueKeysWithValues: stems.map { ($0, CGPoint.zero) })
            for (i, a) in stems.enumerated() {
                for b in stems[(i + 1)...] {
                    var dx = pos[a]!.x - pos[b]!.x
                    var dy = pos[a]!.y - pos[b]!.y
                    let dist = max(20, hypot(dx, dy))
                    let f = 900 / (dist * dist)
                    dx /= dist; dy /= dist
                    forces[a]!.x += f * dx; forces[a]!.y += f * dy
                    forces[b]!.x -= f * dx; forces[b]!.y -= f * dy
                }
            }
            for (a, b) in edges {
                let dx = pos[b]!.x - pos[a]!.x
                let dy = pos[b]!.y - pos[a]!.y
                let dist = max(1, hypot(dx, dy))
                let f = (dist - 90) * 0.02
                forces[a]!.x += f * dx / dist; forces[a]!.y += f * dy / dist
                forces[b]!.x -= f * dx / dist; forces[b]!.y -= f * dy / dist
            }
            for s in stems {
                let cc = clusterCenter(clusterOf[s] ?? 0)
                let fx = (cc.x - pos[s]!.x) * 0.03 + (400 - pos[s]!.x) * 0.005 + forces[s]!.x
                let fy = (cc.y - pos[s]!.y) * 0.03 + (260 - pos[s]!.y) * 0.005 + forces[s]!.y
                pos[s]!.x = min(770, max(30, pos[s]!.x + fx))
                pos[s]!.y = min(490, max(30, pos[s]!.y + fy))
            }
        }
        return pos
    }
}

/// Tiny deterministic RNG (SplitMix64) so the map layout is stable.
struct SeededRandom {
    private var state: UInt64
    init(seed: UInt64) { state = seed }
    mutating func next() -> Double {
        state &+= 0x9E3779B97F4A7C15
        var z = state
        z = (z ^ (z >> 30)) &* 0xBF58476D1CE4E5B9
        z = (z ^ (z >> 27)) &* 0x94D049BB133111EB
        z = z ^ (z >> 31)
        return Double(z >> 11) / Double(1 << 53)
    }
}
