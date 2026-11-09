---
name: brain-learn
description: "Turn a correction from you into a rule or memory entry. Trigger: 'brain: learn <correction>'."
---

# Learn

Corrections are how the brain gets smarter. This skill is the manual
version of open-second-brain's dream pass: a repeated correction
becomes a rule; a one-off correction fixes the record.

## Steps

1. **Fix only what was corrected.** Name the item explicitly. Never
   infer from a pronoun, never "fix" neighboring items.
2. **Strike, don't erase.** Old claim stays, struck through, with its
   source and the date it was believed. New claim gets the new source
   and today's date. History stays readable.
3. **Decide: record or rule?**
   - One-off fact (a number, a date, a name) → fix the note /
     `memory.md` entry, done.
   - Repeated correction (second time the same thing was corrected) →
     it becomes a rule: add it to `rules/` (or to the map, if it
     governs loading), and log it as a `learn` entry.
4. **Propagate.** Search the brain for the old claim in other pages
   (`rg` the key phrase). Fix each occurrence the same way.
5. **Log it.** `## [YYYY-MM-DD] learn | <what changed>` in `log.md`.

## Rules

- You correct the record in all directions, including against
  your own case. Take the correction as given; do not argue it.
- If a correction is unclear (a garbled fragment), ask plainly what
  he meant. Claim no task or follow-up until you confirm it.
- A rule born from a correction names the correction that caused it.
