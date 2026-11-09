---
name: brain-lint
description: "Health-check the wiki: contradictions, stale claims, orphans, missing links. Trigger: 'brain: lint'."
---

# Lint

Karpathy's lint operation: periodically health-check the wiki so it
stays maintained — the LLM does the bookkeeping humans abandon.

## Checks (in order)

1. **Contradictions.** Pages that assert opposite things. List both,
   with sources and dates. Do not resolve them — flag for you.
2. **Stale claims.** A newer source supersedes an older claim that was
   never struck through. List page, old claim, new source.
3. **Orphans.** Pages with no inbound `[[links]]` (from `MAP.md`).
   Inbox notes may be unlinked; everything else should link somewhere.
4. **Missing pages.** Important concepts mentioned in many pages that
   have no page of their own. List the top few by mention count.
5. **Missing cross-references.** Pages that should link each other
   and do not. Suggest the links; add them only if obvious.
6. **Map/rule conflicts.** Any `rules/` entry contradicting `MUSE.md`. The map wins; log the conflict, propose the fix.
7. **Source gaps.** Claims marked `[source needed]` or with no source
   line. List them for the weekly review to chase.

## Output

A short lint report: one section per check, each item one line
(page, problem, source). End with counts. Log the lint run.
Fix only the trivially safe items (a missing obvious link); leave
contradictions and stale claims for your call.
