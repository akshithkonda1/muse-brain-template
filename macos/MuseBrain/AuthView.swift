// AuthView.swift — the sign-in screen for Muse Brain.
//
// Your Muse Brain is a digital copy of your information: after you
// sign in, it builds an interactive memory map from your notes and
// lets you see what Muse knows about you. The login is the door
// into *your* copy — nobody else's.
//
// Honest limitation, stated in the UI and in docs/login.md: there
// is NO public Meta / Muse sign-in endpoint for a local brain yet.
// "Sign in with Muse" is therefore a clearly-labelled placeholder —
// it explains that, sends nothing anywhere, and collects no
// password. The working sign-in is "Continue locally" as the
// profile in brain-profile.json, with an optional local passcode
// stored only on this device as a SHA-256 hash (CryptoKit).
// Signing out clears the session. No account, no cloud, no server.

import CryptoKit
import SwiftUI

/// The signed-in profile for this brain, read from brain-profile.json.
/// Private brain: Akshith. Public template: a clearly-marked Demo.
struct BrainProfile: Codable, Equatable {
    var owner: String = "You"
    var displayName: String = "You"
    var demo: Bool = false
}

struct AuthView: View {
    var profile: BrainProfile
    var onSignIn: () -> Void

    @State private var showMuseNotice = false
    @State private var passcode = ""
    @State private var setPasscode = ""
    @State private var error: String?
    @AppStorage("muse-brain-passcode-hash") private var passcodeHash = ""

    private var hasPasscode: Bool { !passcodeHash.isEmpty }

    private func sha256(_ text: String) -> String {
        SHA256.hash(data: Data(text.utf8)).map { String(format: "%02x", $0) }.joined()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Muse Brain · Your digital copy")
                .font(.caption).bold()
                .textCase(.uppercase)
                .foregroundStyle(.secondary)
            Text("Sign in to your\nMuse Brain.")
                .font(.system(size: 34, weight: .bold))
            Text(profile.demo
                 ? "A demo digital copy — generic example notes only, nothing personal. Sign in to explore what Muse knows in this example brain."
                 : "Your information, as an interactive memory map — what Muse knows about you, with the sources to check it.")
                .foregroundStyle(.secondary)
                .frame(maxWidth: 440, alignment: .leading)

            Button(profile.demo ? "Try the demo — continue locally" : "Continue locally as \(profile.displayName)") {
                if hasPasscode { return } // passcode field below takes over
                onSignIn()
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            Button("Sign in with Muse") { showMuseNotice = true }
                .buttonStyle(.bordered)
                .controlSize(.large)
            if showMuseNotice {
                Text("Sign in with Muse is coming soon. Muse is Meta's personal AI agent, and there is no public Muse / Meta sign-in endpoint for a local brain yet — so this button cannot log you in today, and it will not collect a password or send anything anywhere. It will connect for real when Meta publishes one. For now, continue locally above.")
                    .font(.callout)
                    .padding(10)
                    .background(Color.accentColor.opacity(0.08), in: RoundedRectangle(cornerRadius: 10))
            }

            if hasPasscode {
                SecureField("Local passcode", text: $passcode)
                    .textFieldStyle(.roundedBorder)
                    .frame(maxWidth: 320)
                Button("Unlock") {
                    if sha256(passcode) == passcodeHash { onSignIn() }
                    else { error = "That passcode did not match the one set on this device." }
                }
                .buttonStyle(.bordered)
            } else {
                SecureField("Set a local passcode (optional, 4+ chars)", text: $setPasscode)
                    .textFieldStyle(.roundedBorder)
                    .frame(maxWidth: 320)
                Button("Set passcode & sign in") {
                    if setPasscode.count >= 4 { passcodeHash = sha256(setPasscode) }
                    onSignIn()
                }
                .buttonStyle(.bordered)
            }
            if let error {
                Text(error).foregroundStyle(.red).font(.callout)
            }

            Text("🔒 Everything stays on this device. No account is created, no notes leave this device, no password is sent anywhere. Signing out ends the session." + (profile.demo ? " Demo: this copy holds only generic example notes." : ""))
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(maxWidth: 440, alignment: .leading)
        }
        .padding(40)
        .frame(minWidth: 560, minHeight: 520)
    }
}
