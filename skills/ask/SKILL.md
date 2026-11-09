---
name: brain-ask
description: "Answer a question from the wiki with citations, and file good answers back. Trigger: 'brain: ask <question>'."
---

# Ask

A question answered well is a source. File it back so the next
question does not start from zero (Karpathy: good answers become
new wiki pages).

## Steps

1. Run the `search` skill for the question. Read the pages it finds.
2. **Synthesize, don't list.** Give the actual answer, with citations
   to pages and their sources — not "here are 10 chunks that mention
   your query". Say what the brain does not know yet.
3. **File it back** when the answer is worth keeping: a comparison,
   an analysis, a connection discovered. Write it as an atomic note
   in `notes/` (one idea, one source — the source is the question and
   the pages it drew on — one conclusion), link it from the relevant
   wiki pages, update `index.md`, log it.
4. **Keep tensions visible.** If the pages disagree, show both sides
   and the sources; do not resolve the disagreement quietly.

## Rules

- Cite or it did not happen. An uncited claim is a draft, not an answer.
- If the wiki is silent and `raw/` has nothing either, say so and
  propose the source that would answer it — then stop.
- Never present a brain answer as verified external fact. The brain
  is your record; the world still needs checking.
