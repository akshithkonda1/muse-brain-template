// MuseBrainApp.swift — the app entry point.
//
// macOS 14+, SwiftUI. The app finds the brain folder (saved choice,
// a "Brain" folder next to the .app, ~/MuseBrain, or
// ~/Documents/MuseBrain) and opens it; otherwise it asks you to
// choose one. No server, no cloud — it reads Markdown off disk.

import SwiftUI

@main
struct MuseBrainApp: App {
    @StateObject private var store = BrainStore()

    var body: some Scene {
        WindowGroup {
            if store.brainFolder == nil {
                WelcomeView(store: store)
            } else {
                ContentView(store: store)
            }
        }
        .windowStyle(.titleBar)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}

struct WelcomeView: View {
    @ObservedObject var store: BrainStore

    var body: some View {
        VStack(spacing: 16) {
            Text("Muse Brain")
                .font(.largeTitle).bold()
            Text("A plain folder of Markdown notes, with a map, a scan, " +
                 "and local ML search — no cloud, no account, no server.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
                .frame(maxWidth: 420)
            Button("Choose brain folder…") { store.chooseFolder() }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
            Text("Pick the folder holding your brain (the one with notes/ and MUSE.md). " +
                 "The app reads the Markdown files directly and remembers the choice.")
                .font(.caption).foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 420)
        }
        .padding(40)
        .frame(minWidth: 520, minHeight: 380)
    }
}
