// Models.swift — the data types of the Muse Brain Swift app.
//
// The Markdown files are the source of truth. These structs are just
// the in-memory shape of what BrainStore reads from disk. Nothing
// here talks to a network, a database, or a cloud service.

import Foundation

/// One note (or wiki page) from the brain folder.
struct Note: Identifiable, Hashable {
    let stem: String          // filename without .md, e.g. "garden-notes"
    let title: String         // first "# ..." line, or the stem
    let tags: [String]        // "#tag" values, e.g. ["people"]
    let links: [String]       // [[wiki-link]] targets, normalized stems
    let text: String          // raw Markdown, as read from disk
    let fileURL: URL
    let area: String          // "notes" or "wiki"
    let modified: Date

    var id: String { stem }
}

/// One topic cluster from the ML step.
struct Cluster: Identifiable, Hashable {
    let label: String         // top terms, e.g. "lexus, company, parents"
    let members: [String]     // note stems
    var id: String { label }
}

/// One unlinked pair worth linking.
struct LinkSuggestion: Identifiable, Hashable {
    let a: String
    let b: String
    let cosine: Double
    let sharedTags: [String]
    var id: String { a + "<->" + b }
}

/// A pair the duplicate check flagged.
struct DuplicateFlag: Identifiable, Hashable {
    let a: String
    let b: String
    let kind: String          // "exact" / "likely-duplicate (Jaccard)" / "near-duplicate (semantic)"
    let score: Double
    var id: String { a + "~" + b }
}
