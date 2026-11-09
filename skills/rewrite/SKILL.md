---
name: brain-rewrite
description: "Tighten a brain page in your voice, keeping sources and tensions. Trigger: 'brain: rewrite <page>'."
---

# Rewrite

Rewrite for clarity and voice, never for length alone. The bar: revisions must make sense and not read like AI
slop — human, in-voice, de-slopped.

## Steps

1. Read the page and the sources it cites. Read `rules/writing.md`.
2. **Cut filler, keep facts.** Every bullet must add evidence,
   mechanism, example, implication, or a decision. If it adds none,
   cut it.
3. **Keep your words.** Verbatim quotes that carry a decision stay
   verbatim. Do not paraphrase a decision into mush.
4. **Keep sources attached.** A fact that loses its source in the
   rewrite is a fact lost. Re-attach or revert.
5. **Keep tensions visible.** Do not smooth a live disagreement into
   a false consensus. Both sides stay, with sources.
6. **Keep the shape.** Title, tight bullets, open threads, `Tags:`
   line, `[[links]]`. Do not reformat a note into an essay.
7. Log the rewrite (`## [YYYY-MM-DD] rewrite | <page>`) and run
   `python3 scan.py` if links or tags changed.

## Do not

- Do not invent frameworks, pillars, or numbered taxonomies.
- Do not add a "bottom line" section. The first line is the point.
- Do not rewrite a page you have not asked about, and never
  rewrite `raw/` — raw is immutable.
