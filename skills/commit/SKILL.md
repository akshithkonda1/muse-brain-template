---
name: brain-commit
description: "Review the diff, commit the brain with a short summary. Trigger: 'brain: commit'."
---

# Commit

The brain is a Git repo. Commit weekly, or after
any ingest batch. Never push without your go-ahead.

## Steps

1. **Status.** `git status --short` and `git diff --stat`. Read the
   actual diff — never commit blind, never commit from a summary.
2. **Review the diff for leaks.** No secrets, keys, credentials, or
   health detail beyond what the brain already holds by design. No
   work-confidential material you did not explicitly put here. If
   anything looks wrong, stop and ask — do not commit it.
3. **Check the rules.** `raw/` files are immutable — a diff touching
   a committed `raw/` file is a red flag, not a routine edit.
   Confirm the map is still under 200 lines.
4. **Commit** with a short message and a ≤200-word summary body:
   what was ingested, what changed, what is still open. Example:
   `git commit -m "Brain: ingest X, update Y" -m "<summary>"`
5. **Log it.** `## [YYYY-MM-DD] commit | <summary>` in `log.md`.
6. **Push only on your word.** `git push` needs your explicit go-ahead
   each time until you say otherwise. Never push personal notes to a public remote — only this template shape is public.

## Rules

- One commit per review cycle, not one per file.
- Never force-push. Never rewrite history — the log is the point.
- If the repo remote is not the repo you expect, do not
  push at all. Report that instead.
