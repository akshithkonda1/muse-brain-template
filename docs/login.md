# Login — sign in to your Muse Brain

Your Muse Brain is a **digital copy of your information**: after you sign
in, it builds an interactive memory map from your notes and lets you
interact with your data and see what Muse knows about you. The login is
the door into *your* copy — nobody else's.

## What signing in unlocks

- The full memory map: every note, link, cluster, and hub, generated
  from your Markdown files.
- **What Muse knows**: a browsable view of your information by area
  (people, projects, money, goals, places, ideas…), where every topic
  shows its note, its sources, and what Muse knows about it — with a
  source trail you can check.
- Search and Ask over the map (local TF-IDF/BM25 ML), related notes,
  and link suggestions.

Signing in changes nothing about your notes. It does not edit, upload,
or share them. It only unlocks the view on this device.

## How sign-in works (local-first)

There is **no public Meta / Muse OAuth endpoint for Muse Brain to
call today**. Muse is Meta's personal AI agent, and no sign-in
endpoint for a local brain has been published. So this app does **not**
fake a Meta login:

- The **"Sign in with Muse"** button is clearly labelled as coming
  soon. Tapping it explains, in plain words, that there is no public
  Muse/Meta sign-in endpoint yet, that nothing was sent anywhere, and
  that it will connect for real when Meta publishes one. It never
  collects a password and never sends credentials anywhere.
- The working sign-in is **Continue locally**: you open your own
  brain on this device, as your local profile (in the private brain:
  Akshith; in the public template: a clearly-marked Demo profile).
  Optionally you can set a **local passcode** (4+ characters). It is
  stored only on this device, only as a SHA-256 hash, never in the
  repo, never sent anywhere. Forgetting it just means clearing the
  app's local data and signing in again — there is no recovery, by
  design, because there is no server to recover from.
- Signing out clears the session. Closing the tab / app also ends
  the web session.

The local app server (`app/app.py`) binds to `127.0.0.1` only — it is
reachable from this machine and no other. The login gate is in the
frontends (dashboard, Swift Mac app, React Native Windows app), not
in the server, because the server never leaves localhost.

## The future path to real Muse / Meta SSO

When Meta publishes a sign-in endpoint for Muse, the swap is small
and contained:

1. The "Sign in with Muse" button calls the real endpoint instead of
   showing the notice.
2. The returned Muse account identity replaces the local profile
   name — the rest of the app (map, knows view, search) does not
   change, because it already keys everything off the signed-in
   profile.
3. The local passcode stays as an optional second step on the
   device; it never becomes a cloud password.

Until then, do not wire any third-party login in by hand, and do not
paste a Meta password or token into this repo or any of its apps.

## Privacy by design

- The digital copy lives **locally**: Markdown files + a local ML
  index (gitignored caches). It never uploads to a cloud.
- It never leaves the device unless you push the private repo
  yourself (and the public template contains only generic example
  notes — see the scrub audit in `SCRUB-REPORT.md`).
- The login creates **no cloud account** and sends your notes
  nowhere. There is no telemetry, no analytics, no tracking.
- A passcode hash is the only credential material, and it lives in
  the browser / OS local storage on the device — never in git.

## Per-frontend notes

- **Web dashboard** (`dashboard.html`, from `app/dashboard-template.html`):
  a full-screen premium login gate (same design system: warm paper /
  ink dark, violet accent). Session in `sessionStorage`; theme in
  `localStorage`; passcode hash in `localStorage` under
  `muse-brain-passcode-hash`. Sign out is in the header.
- **macOS Swift app** (`macos/`): `AuthView.swift` login screen,
  session in `@AppStorage("muse-brain-signed-in")`, passcode hash in
  `UserDefaults` under `muse-brain-passcode-hash` (SHA-256 via
  CryptoKit). "Sign in with Muse" shows the honest notice as an
  alert.
- **Windows React Native app** (`windows-app/`): `src/Login.tsx`
  login screen, session in memory only for v1 (no persistent store
  is bundled — signing out or closing the app ends the session).
  The passcode step is not persisted in the Windows build; the
  login screen says so plainly.

## Commands

- `brain: login` — open the sign-in screen (or explain the login
  design, if you are already signed in).
- `brain: knows <topic>` — what Muse knows about a topic, with its
  sources. See `skills/what-muse-knows/SKILL.md`.
