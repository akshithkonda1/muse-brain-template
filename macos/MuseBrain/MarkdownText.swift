// MarkdownText.swift — renders a note's Markdown with plain SwiftUI.
//
// Uses AttributedString's Markdown support (macOS 12+) for headings,
// bold/italic, lists, and code. [[wiki-links]] are rewritten to
// brain:// links first, so taps navigate inside the app instead of
// opening a browser. Falls back to plain text if parsing fails.

import SwiftUI

struct MarkdownText: View {
    let markdown: String
    let onOpenNote: (String) -> Void

    var body: some View {
        Group {
            if let attributed = try? AttributedString(
                markdown: Self.rewritten(markdown),
                options: AttributedString.MarkdownParsingOptions(
                    interpretedSyntax: .full)) {
                Text(attributed)
            } else {
                Text(markdown)
            }
        }
        .textSelection(.enabled)
        .environment(\.openURL, OpenURLAction { url in
            if url.scheme == "brain", let stem = url.host {
                onOpenNote(stem)
                return .handled
            }
            return .systemAction
        })
    }

    /// [[target]] -> [target](brain://target); leaves code spans alone
    /// well enough for note text (notes rarely nest links in code).
    static func rewritten(_ text: String) -> String {
        var out = text
        let pattern = "\\[\\[([^\\]|#]+)(?:#[^\\]]*)?(?:\\|[^\\]]*)?\\]\\]"
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return text }
        let range = NSRange(out.startIndex..., in: out)
        var result = ""
        var lastEnd = out.startIndex
        for match in regex.matches(in: out, range: range) {
            guard let whole = Range(match.range, in: out),
                  let inner = Range(match.range(at: 1), in: out) else { continue }
            let target = String(out[inner]).trimmingCharacters(in: .whitespaces)
            let stem = target.lowercased().replacingOccurrences(of: " ", with: "-")
            result += out[lastEnd..<whole.lowerBound]
            result += "[\(target)](brain://\(stem))"
            lastEnd = whole.upperBound
        }
        result += out[lastEnd...]
        return result
    }
}
