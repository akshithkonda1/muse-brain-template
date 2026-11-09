// SearchEngine.swift — local ML search, ported from ml/search.py.
//
// Same math as the Python baseline, so the Swift app ranks the same
// way the Python tool does: BM25 (primary) + TF-IDF cosine (second
// signal), greedy topic clusters, Jaccard + cosine duplicates.
// Stdlib / Foundation only. No network, no API, no model download.

import Foundation

enum SearchEngine {
    static let stopwords: Set<String> = [
        "a", "an", "the", "and", "or", "of", "to", "in", "on", "for",
        "with", "is", "are", "was", "were", "be", "by", "at", "as",
        "it", "its", "this", "that", "these", "those", "from", "into",
        "over", "under", "after", "before", "not", "no", "nor", "but",
        "if", "then", "than", "so", "such", "can", "could", "will",
        "would", "should", "he", "she", "they", "we", "you", "i",
        "his", "her", "their", "our", "your", "my", "me", "him",
        "them", "us", "what", "which", "who", "whom", "when", "where",
        "why", "how", "all", "any", "both", "each", "few", "more",
        "most", "other", "some", "such", "only", "own", "same", "too",
        "very", "just", "also",
    ]

    static let negationMarkers: Set<String> = [
        "not", "never", "no", "out", "dropped", "cancelled", "canceled",
        "versus", "vs", "instead", "tension", "conflict", "contradicts",
    ]

    /// Tokenize like the Python side: lowercase words, drop stopwords.
    static func tokenize(_ text: String) -> [String] {
        var cleaned = text
        // Strip code fences and expand [[links]] to words.
        cleaned = cleaned.replacingOccurrences(
            of: "```[\\s\\S]*?```", with: " ", options: .regularExpression)
        cleaned = cleaned.replacingOccurrences(
            of: "\\[\\[([^\\]|#]+)(?:#[^\\]]*)?(?:\\|[^\\]]*)?\\]\\]",
            with: " $1 ", options: .regularExpression)
        let words = cleaned.lowercased().components(separatedBy:
            CharacterSet.alphanumerics.inverted)
        return words.filter { $0.count > 1 && !stopwords.contains($0) }
    }

    /// The searchable index over a set of notes.
    struct Index {
        let notes: [Note]
        let idf: [String: Double]
        let avgdl: Double
        let tfidf: [String: [String: Double]]   // stem -> normalized vector
        let counts: [String: [String: Int]]     // stem -> term counts
        let docLen: [String: Int]

        init(notes: [Note]) {
            self.notes = notes
            var df: [String: Int] = [:]
            var counts: [String: [String: Int]] = [:]
            var docLen: [String: Int] = [:]
            for note in notes {
                var c: [String: Int] = [:]
                for token in SearchEngine.tokenize(note.text) { c[token, default: 0] += 1 }
                counts[note.stem] = c
                docLen[note.stem] = c.values.reduce(0, +)
                for term in c.keys { df[term, default: 0] += 1 }
            }
            self.counts = counts
            self.docLen = docLen
            let n = Double(max(notes.count, 1))
            var idf: [String: Double] = [:]
            for (term, d) in df {
                idf[term] = log((n - Double(d) + 0.5) / (Double(d) + 0.5) + 1)
            }
            self.idf = idf
            self.avgdl = notes.isEmpty ? 0 :
                Double(docLen.values.reduce(0, +)) / Double(notes.count)
            var tfidf: [String: [String: Double]] = [:]
            for note in notes {
                var vec: [String: Double] = [:]
                for (term, tf) in counts[note.stem] ?? [:] {
                    vec[term] = (1 + log(Double(tf))) * (idf[term] ?? 0)
                }
                let norm = sqrt(vec.values.map { $0 * $0 }.reduce(0, +))
                tfidf[note.stem] = norm > 0
                    ? vec.mapValues { $0 / norm } : vec
            }
            self.tfidf = tfidf
        }

        func cosine(_ a: [String: Double], _ b: [String: Double]) -> Double {
            var sum = 0.0
            let small = a.count <= b.count ? a : b
            let large = a.count <= b.count ? b : a
            for (term, v) in small { sum += v * (large[term] ?? 0) }
            return sum
        }

        /// Ranked search: BM25 primary, TF-IDF cosine second.
        func search(_ query: String, top: Int = 8) -> [(note: Note, score: Double, bm25: Double, cosine: Double)] {
            let qterms = SearchEngine.tokenize(query)
            guard !qterms.isEmpty else { return [] }
            var qvec: [String: Double] = [:]
            var qcounts: [String: Int] = [:]
            for t in qterms { qcounts[t, default: 0] += 1 }
            for (term, tf) in qcounts {
                if let id = idf[term] { qvec[term] = (1 + log(Double(tf))) * id }
            }
            let qnorm = sqrt(qvec.values.map { $0 * $0 }.reduce(0, +))
            if qnorm > 0 { qvec = qvec.mapValues { $0 / qnorm } }
            let k1 = 1.5, b = 0.75
            var out: [(Note, Double, Double, Double)] = []
            for note in notes {
                var bm25 = 0.0
                let dl = Double(docLen[note.stem] ?? 1)
                for term in Set(qterms) {
                    let tf = counts[note.stem]?[term] ?? 0
                    guard tf > 0, let id = idf[term] else { continue }
                    let denom = Double(tf) + k1 * (1 - b + b * dl / max(avgdl, 1))
                    bm25 += id * Double(tf) * (k1 + 1) / denom
                }
                let cos = cosine(qvec, tfidf[note.stem] ?? [:])
                let score = bm25 + cos
                if score > 0 { out.append((note, score, bm25, cos)) }
            }
            return out.sorted { $0.1 > $1.1 }.prefix(top).map { $0 }
        }

        /// Notes most similar to one note (TF-IDF cosine).
        func related(to stem: String, top: Int = 5) -> [(note: Note, cosine: Double)] {
            guard let target = tfidf[stem] else { return [] }
            return notes.filter { $0.stem != stem }
                .map { ($0, cosine(target, tfidf[$0.stem] ?? [:])) }
                .filter { $0.1 > 0 }
                .sorted { $0.1 > $1.1 }
                .prefix(top).map { $0 }
        }

        /// Unlinked pairs worth linking (cosine >= 0.20).
        func suggestLinks(threshold: Double = 0.20) -> [LinkSuggestion] {
            var out: [LinkSuggestion] = []
            for (i, a) in notes.enumerated() {
                for b in notes[(i + 1)...] {
                    if b.links.contains(a.stem) || a.links.contains(b.stem) { continue }
                    let cos = cosine(tfidf[a.stem] ?? [:], tfidf[b.stem] ?? [:])
                    if cos >= threshold {
                        out.append(LinkSuggestion(
                            a: a.stem, b: b.stem, cosine: cos,
                            sharedTags: Array(Set(a.tags).intersection(b.tags)).sorted()))
                    }
                }
            }
            return out.sorted { $0.cosine > $1.cosine }
        }

        /// Greedy agglomerative clustering (cosine >= 0.15 joins a cluster).
        func clusters(threshold: Double = 0.15) -> [Cluster] {
            var groups: [[Note]] = []
            for note in notes {
                var best: Int? = nil
                var bestCos = 0.0
                for (i, g) in groups.enumerated() {
                    let cos = g.map { cosine(tfidf[note.stem] ?? [:], tfidf[$0.stem] ?? [:]) }.max() ?? 0
                    if cos > bestCos { best = i; bestCos = cos }
                }
                if let i = best, bestCos >= threshold { groups[i].append(note) }
                else { groups.append([note]) }
            }
            return groups.map { g in
                var agg: [String: Double] = [:]
                for note in g {
                    for (term, w) in tfidf[note.stem] ?? [:] { agg[term, default: 0] += w }
                }
                let label = agg.sorted { $0.value > $1.value }.prefix(3)
                    .map { $0.key }.joined(separator: ", ")
                return Cluster(label: label.isEmpty ? "(no terms)" : label,
                               members: g.map { $0.stem })
            }.sorted { $0.members.count > $1.members.count }
        }

        /// Exact + Jaccard (> 0.72) + semantic (cosine > 0.85) duplicates.
        func duplicates() -> [DuplicateFlag] {
            var out: [DuplicateFlag] = []
            func wordSet(_ note: Note) -> Set<String> {
                Set(SearchEngine.tokenize(note.text))
            }
            for (i, a) in notes.enumerated() {
                for b in notes[(i + 1)...] {
                    if a.text == b.text {
                        out.append(DuplicateFlag(a: a.stem, b: b.stem, kind: "exact", score: 1.0))
                        continue
                    }
                    let wa = wordSet(a), wb = wordSet(b)
                    let jac = Double(wa.intersection(wb).count) /
                        Double(max(wa.union(wb).count, 1))
                    let cos = cosine(tfidf[a.stem] ?? [:], tfidf[b.stem] ?? [:])
                    if jac > 0.72 {
                        out.append(DuplicateFlag(a: a.stem, b: b.stem,
                                                 kind: "likely-duplicate (Jaccard)", score: jac))
                    } else if cos > 0.85 {
                        out.append(DuplicateFlag(a: a.stem, b: b.stem,
                                                 kind: "near-duplicate (semantic)", score: cos))
                    }
                }
            }
            return out
        }
    }
}
